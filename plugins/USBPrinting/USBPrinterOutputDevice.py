# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from .avr_isp import stk500v2, ispBase, intelHex
import serial   # type: ignore
import threading
import time
import queue
import re
import functools
import os
import urllib.request, json, codecs

from UM.Application import Application
from UM.Logger import Logger
from cura.PrinterOutputDevice import PrinterOutputDevice, ConnectionState
from UM.Message import Message
from cura.FirmwareVersion import FirmwareVersion

from PyQt5.QtCore import QUrl, pyqtSlot, pyqtSignal, pyqtProperty

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class USBPrinterOutputDevice(PrinterOutputDevice):
    def __init__(self, serial_port):
        super().__init__(serial_port)
        self.setName(catalog.i18nc("@item:inmenu", "USB printing"))
        self.setShortDescription(catalog.i18nc("@action:button Preceded by 'Ready to'.", "Print via USB"))
        self.setDescription(catalog.i18nc("@info:tooltip", "Print via USB"))
        self.setIconName("print")
        self.setConnectionText(catalog.i18nc("@info:status", "Connected via USB"))

        self._global_stack = None

        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)

        self._serial = None
        self._serial_port = serial_port
        self._error_state = None

        self._connect_thread = threading.Thread(target = self._connect)
        self._connect_thread.daemon = True

        self._end_stop_thread = None
        self._poll_endstop = False

        # The baud checking is done by sending a number of m105 commands to the printer and waiting for a readable
        # response. If the baudrate is correct, this should make sense, else we get giberish.
        self._required_responses_auto_baud = 3

        self._listen_thread = threading.Thread(target=self._listen)
        self._listen_thread.daemon = True

        self._update_firmware_thread = threading.Thread(target= self._updateFirmware)
        self._update_firmware_thread.daemon = True
        self.firmwareUpdateComplete.connect(self._onFirmwareUpdateComplete)

        self._heatup_wait_start_time = time.time()

        ## Queue for commands that need to be send. Used when command is sent when a print is active.
        self._command_queue = queue.Queue()

        self._is_printing = False
        self._is_paused = False

        ## Set when print is started in order to check running time.
        self._print_start_time = None
        self._print_start_time_100 = None

        ## Keep track where in the provided g-code the print is
        self._gcode_position = 0

        # List of gcode lines to be printed
        self._gcode = []

        # Check if endstops are ever pressed (used for first run)
        self._x_min_endstop_pressed = False
        self._y_min_endstop_pressed = False
        self._z_min_endstop_pressed = False

        self._x_max_endstop_pressed = False
        self._y_max_endstop_pressed = False
        self._z_max_endstop_pressed = False

        # In order to keep the connection alive we request the temperature every so often from a different extruder.
        # This index is the extruder we requested data from the last time.
        self._temperature_requested_extruder_index = 0

        self._current_z = 0

        self._updating_firmware = False

        self._firmware_file_name = None
        self._firmware_update_finished = False

        self._error_message = None
        self._error_code = 0
        
        self._firmware_version = None
        self._firmware_latest_version = None
        self._version_command_sent = False

        self._tmp_file = False

        self._machine_dict = {
            "bcn3dsigma": {
                "latest_release_api": "http://api.github.com/repos/bcn3d/bcn3dsigma-firmware/releases/latest"
            },
            "bcn3dsigmax": {
                "latest_release_api": "http://api.github.com/repos/bcn3d/bcn3dsigmax-firmware/releases/latest"
            }
        }

        self._onGlobalStackChanged()

    onError = pyqtSignal()

    firmwareUpdateComplete = pyqtSignal()
    firmwareUpdateChange = pyqtSignal()

    firmwareChange = pyqtSignal()
    firmwareLatestChange = pyqtSignal()

    endstopStateChanged = pyqtSignal(str ,bool, arguments = ["key","state"])

    def _onGlobalStackChanged(self):
        self._global_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_stack:
            self._getFirmwareLatestVersion()
            if self._connection_state == ConnectionState.closed and not self._connect_thread.isAlive():
                self._connect_thread.start()

    def _setTargetBedTemperature(self, temperature):
        Logger.log("d", "Setting bed temperature to %s", temperature)
        self._sendCommand("M140 S%s" % temperature)

    def _setTargetHotendTemperature(self, index, temperature):
        Logger.log("d", "Setting hotend %s temperature to %s", index, temperature)
        self._sendCommand("M104 T%s S%s" % (index, temperature))

    def _setHeadPosition(self, x, y , z, speed):
        self._sendCommand("G0 X%s Y%s Z%s F%s" % (x, y, z, speed))

    def _setHeadX(self, x, speed):
        self._sendCommand("G0 X%s F%s" % (x, speed))

    def _setHeadY(self, y, speed):
        self._sendCommand("G0 Y%s F%s" % (y, speed))

    def _setHeadZ(self, z, speed):
        self._sendCommand("G0 Y%s F%s" % (z, speed))

    def _homeHead(self):
        self._sendCommand("G28 X0 Y0")

    def _homeBed(self):
        self._sendCommand("G28")

    ##  A name for the device.
    @pyqtProperty(str, constant = True)
    def name(self):
        return self.getName()

    ##  The address of the device.
    @pyqtProperty(str, constant = True)
    def address(self):
        return self._serial_port

    @pyqtProperty(str, notify=firmwareChange)
    def firmwareVersion(self):
        return str(self._firmware_version)
        
    @pyqtProperty(str, notify=firmwareLatestChange)
    def firmwareLatestVersion(self):
        return str(self._firmware_latest_version)

    def startPrint(self):
        self.writeStarted.emit(self)
        gcode_list = getattr( Application.getInstance().getController().getScene(), "gcode_list")
        self._updateJobState("printing")
        self.printGCode(gcode_list)

    def _moveHead(self, x, y, z, speed):
        self._sendCommand("G91")
        self._sendCommand("G0 X%s Y%s Z%s F%s" % (x, y, z, speed))
        self._sendCommand("G90")

    ##  Start a print based on a g-code.
    #   \param gcode_list List with gcode (strings).
    def printGCode(self, gcode_list):
        Logger.log("d", "Started printing g-code")
        if self._progress or self._connection_state != ConnectionState.connected:
            self._error_message = Message(catalog.i18nc("@info:status", "Unable to start a new job because the printer is busy or not connected."))
            self._error_message.show()
            Logger.log("d", "Printer is busy or not connected, aborting print")
            self.writeError.emit(self)
            return

        self._gcode.clear()
        for layer in gcode_list:
            self._gcode.extend(layer.split("\n"))

        # Reset line number. If this is not done, first line is sometimes ignored
        self._gcode.insert(0, "M110")
        self._gcode_position = 0
        self._print_start_time_100 = None
        self._is_printing = True
        self._print_start_time = time.time()

        for i in range(0, 4):  # Push first 4 entries before accepting other inputs
            self._sendNextGcodeLine()

        self.writeFinished.emit(self)

    ##  Get the serial port string of this connection.
    #   \return serial port
    def getSerialPort(self):
        return self._serial_port

    ##  Try to connect the serial. This simply starts the thread, which runs _connect.
    def connect(self):
        if not self._updating_firmware and not self._connect_thread.isAlive() and self._global_stack is not None:
            self._connect_thread.start()

    ##  Private function (threaded) that actually uploads the firmware.
    def _updateFirmware(self):
        Logger.log("d", "Attempting to update firmware")
        self._error_code = 0
        self.setProgress(0, 100)
        self._firmware_update_finished = False
        if self._connection_state != ConnectionState.closed:
            self.close()

        if self._firmware_file_name == "":
            self._tmp_file = True
            headers = {
                "User-Agent": "BCN3D Cura"
            }
            machine_id = self._global_stack.getBottom().getId()
            if self._machine_dict.get(machine_id):
                latest_release_url_api = self._machine_dict[machine_id]["latest_release_api"]
            else:
                Logger.log("e", "Unable to get latest release for %s", machine_id)
                self._updateFirmwareFailedMissingFirmware()
                return
            request = urllib.request.Request(latest_release_url_api, headers=headers)
            try:
                latest_release = urllib.request.urlopen(request)
            except Exception as e:
                Logger.log("e", "Exception when getting the download url from github: %s", repr(e))
                self._updateFirmwareFailedMissingFirmware()
                return
            reader = codecs.getreader("utf-8")
            data = json.load(reader(latest_release))

            if self._firmware_version is None or self._firmware_version.isPrerelease() or self._firmware_latest_version > self._firmware_version:
                Logger.log("d", "Dowloading the firmware latest version")
                download_url = None
                for asset in data["assets"]:
                    if asset["name"].endswith(".hex"):
                        download_url = asset["browser_download_url"]
                if download_url:
                    try:
                        self._firmware_file_name, headers = urllib.request.urlretrieve(download_url)
                    except Exception as e:
                        Logger.log("e", "Exception when downloading the firmware from github: %s", repr(e))
                        self._updateFirmwareFailedMissingFirmware()
                        return
                if self._firmware_file_name is None:
                    Logger.log("e", "Unable to download firmware latest version")
                    self._updateFirmwareFailedMissingFirmware()
                    return
                Logger.log("d", "Firmware file stored in temp file: %s", self._firmware_file_name)
            else:
                Logger.log("i", "You already have the latest firmware version (%s) installed", self._firmware_latest_version)
                self._updateFirmwareLatestVersionUploaded()
                return

        hex_file = intelHex.readHex(self._firmware_file_name)

        if len(hex_file) == 0:
            Logger.log("e", "Unable to read provided hex file. Could not update firmware")
            self._updateFirmwareFailedMissingFirmware()
            return

        programmer = stk500v2.Stk500v2()
        programmer.progress_callback = self.setProgress

        try:
            programmer.connect(self._serial_port)
        except Exception:
            programmer.close()
            pass

        # Give programmer some time to connect. Might need more in some cases, but this worked in all tested cases.
        time.sleep(1)

        if not programmer.isConnected():
            Logger.log("e", "Unable to connect with serial. Could not update firmware")
            self._updateFirmwareFailedCommunicationError()
            return

        self._updating_firmware = True

        try:
            programmer.programChip(hex_file)
            self._updating_firmware = False
        except serial.SerialException as e:
            Logger.log("e", "SerialException while trying to update firmware: <%s>" %(repr(e)))
            self._updateFirmwareFailedIOError()
            return
        except Exception as e:
            Logger.log("e", "Exception while trying to update firmware: <%s>" %(repr(e)))
            self._updateFirmwareFailedUnknown()
            return
        programmer.close()

        self._updateFirmwareCompletedSucessfully()
        return

    def _updateFirmwareLatestVersionUploaded(self):
        return self._updateFirmwareFailedCommon(5)

    ##  Private function which makes sure that firmware update process has failed by missing firmware
    def _updateFirmwareFailedMissingFirmware(self):
        return self._updateFirmwareFailedCommon(4)

    ##  Private function which makes sure that firmware update process has failed by an IO error
    def _updateFirmwareFailedIOError(self):
        return self._updateFirmwareFailedCommon(3)

    ##  Private function which makes sure that firmware update process has failed by a communication problem
    def _updateFirmwareFailedCommunicationError(self):
        return self._updateFirmwareFailedCommon(2)

    ##  Private function which makes sure that firmware update process has failed by an unknown error
    def _updateFirmwareFailedUnknown(self):
        return self._updateFirmwareFailedCommon(1)

    ##  Private common function which makes sure that firmware update process has completed/ended with a set progress state
    def _updateFirmwareFailedCommon(self, code):
        if not code:
            raise Exception("Error code not set!")

        self._error_code = code

        self._firmware_update_finished = True
        self.resetFirmwareUpdate(update_has_finished = True)
        self.progressChanged.emit()
        self.firmwareUpdateComplete.emit()
        if self._tmp_file and code != 5:
            self._deleteTmpFile()
        return

    ##  Private function which makes sure that firmware update process has successfully completed
    def _updateFirmwareCompletedSucessfully(self):
        self._firmware_version = None
        self.firmwareChange.emit()
        self.setProgress(100, 100)
        self._firmware_update_finished = True
        self.resetFirmwareUpdate(update_has_finished = True)
        self.firmwareUpdateComplete.emit()
        if self._tmp_file:
            self._deleteTmpFile()
        return

    def _deleteTmpFile(self):
        os.remove(self._firmware_file_name)
        Logger.log("d", "Firmware file deleted: %s", self._firmware_file_name)

    ##  Upload new firmware to machine
    #   \param filename full path of firmware file to be uploaded
    def updateFirmware(self, file_name):
        Logger.log("i", "Updating firmware of %s", self._serial_port)
        self._firmware_file_name = file_name
        self._update_firmware_thread.start()

    @property
    def firmwareUpdateFinished(self):
        return self._firmware_update_finished

    def resetFirmwareUpdate(self, update_has_finished = False):
        self._firmware_update_finished = update_has_finished
        self.firmwareUpdateChange.emit()

    @pyqtSlot()
    def startPollEndstop(self):
        if not self._poll_endstop:
            self._poll_endstop = True
            if self._end_stop_thread is None:
                self._end_stop_thread = threading.Thread(target=self._pollEndStop)
                self._end_stop_thread.daemon = True
            self._end_stop_thread.start()

    @pyqtSlot()
    def stopPollEndstop(self):
        self._poll_endstop = False
        self._end_stop_thread = None

    def _pollEndStop(self):
        while self._connection_state == ConnectionState.connected and self._poll_endstop:
            self.sendCommand("M119")
            time.sleep(0.5)

    ##  Private connect function run by thread. Can be started by calling connect.
    def _connect(self):
        self._global_stack = Application.getInstance().getGlobalContainerStack()
        Logger.log("d", "Attempting to connect to %s", self._serial_port)
        self.setConnectionState(ConnectionState.connecting)
        programmer = stk500v2.Stk500v2()
        try:
            programmer.connect(self._serial_port) # Connect with the serial, if this succeeds, it's an arduino based usb device.
            self._serial = programmer.leaveISP()
        except ispBase.IspError as e:
            programmer.close()
            Logger.log("i", "Could not establish connection on %s: %s. Device is not arduino based." %(self._serial_port,str(e)))
        except Exception as e:
            programmer.close()
            Logger.log("i", "Could not establish connection on %s, unknown reasons.  Device is not arduino based." % self._serial_port)

        baudrate = self._global_stack.getProperty("baudrate", "value")

        if self._serial is None:
            try:
                self._serial = serial.Serial(str(self._serial_port), baudrate, timeout = 3, writeTimeout = 10000)
                time.sleep(10)
            except serial.SerialException:
                Logger.log("d", "Could not open port %s and baudrate %d" % self._serial_port, baudrate)
                self.close()
                self.setConnectionState(ConnectionState.closed)
                return
        elif not self.setBaudRate(baudrate):
            Logger.log("d", "Could not open port %s and baudrate %d" % self._serial_port, baudrate)
            self.close()
            self.setConnectionState(ConnectionState.closed)
            return

        self._serial.timeout = 2  # Reset serial timeout
        self.setConnectionState(ConnectionState.connected)
        self._listen_thread.start()  # Start listening
        Logger.log("i", "Established printer connection on port %s" % (self._serial_port))

    def _getFirmwareVersion(self, line):
        try:
            m115_response = re.search("FIRMWARE_NAME", line.decode("utf-8"))
        except:
            return
        if m115_response:
            result = re.search("(?<=FIRMWARE_VERSION:).+?(?=;)", line.decode("utf-8"))
            if result is None:
                self._firmware_version = "UNKNOWN"
            else:
                self._firmware_version = FirmwareVersion(result.group(0))
            Logger.log("i", "Current firmware version: %s", self._firmware_version)
            if str(self._firmware_version) != "UNKNOWN" and self._firmware_version.isPrerelease():
                Logger.log("i", "Your current firmware version is a prerelease")
            self._version_command_sent = False
            self.firmwareChange.emit()

    def _getFirmwareLatestVersion(self):
        headers = {
            "User-Agent": "BCN3D Cura"
        }
        machine_id = self._global_stack.getBottom().getId()
        if self._machine_dict.get(machine_id):
            latest_release_url_api = self._machine_dict[machine_id]["latest_release_api"]
        else:
            self._firmware_latest_version = "UNKNOWN"
            return
        request = urllib.request.Request(latest_release_url_api, headers=headers)
        try:
            latest_release = urllib.request.urlopen(request)
        except Exception as e:
            Logger.log("e", "Exception trying to get firmware latest version from github: %s", repr(e))
            self._firmware_latest_version = "UNKNOWN"
            return
        reader = codecs.getreader("utf-8")
        data = json.load(reader(latest_release))
        self._firmware_latest_version = FirmwareVersion(data["tag_name"])
        self.firmwareLatestChange.emit()

    ##  Set the baud rate of the serial. This can cause exceptions, but we simply want to ignore those.
    def setBaudRate(self, baud_rate):
        try:
            self._serial.baudrate = baud_rate
            return True
        except Exception as e:
            return False

    ##  Close the printer connection
    def close(self):
        Logger.log("d", "Closing the USB printer connection.")
        if self._connect_thread.isAlive():
            try:
                self._connect_thread.join()
            except Exception as e:
                Logger.log("d", "PrinterConnection.close: %s (expected)", e)
                pass # This should work, but it does fail sometimes for some reason

        self._connect_thread = threading.Thread(target = self._connect)
        self._connect_thread.daemon = True

        self.setConnectionState(ConnectionState.closed)
        if self._serial is not None:
            try:
                self._listen_thread.join()
            except:
                pass
            self._serial.close()

        self._listen_thread = threading.Thread(target = self._listen)
        self._listen_thread.daemon = True
        self._serial = None

    ##  Directly send the command, withouth checking connection state (eg; printing).
    #   \param cmd string with g-code
    def _sendCommand(self, cmd):
        if self._serial is None:
            return

        if "M109" in cmd or "M190" in cmd:
            self._heatup_wait_start_time = time.time()

        try:
            command = (cmd + "\n").encode()
            self._serial.write(b"\n")
            self._serial.write(command)
        except serial.SerialTimeoutException:
            Logger.log("w","Serial timeout while writing to serial port, trying again.")
            try:
                time.sleep(0.5)
                self._serial.write((cmd + "\n").encode())
            except Exception as e:
                Logger.log("e","Unexpected error while writing serial port %s " % e)
                self._setErrorState("Unexpected error while writing serial port %s " % e)
                self.close()
        except Exception as e:
            Logger.log("e","Unexpected error while writing serial port %s" % e)
            self._setErrorState("Unexpected error while writing serial port %s " % e)
            self.close()

    ##  Send a command to printer.
    #   \param cmd string with g-code
    def sendCommand(self, cmd):
        if self._progress:
            self._command_queue.put(cmd)
        elif self._connection_state == ConnectionState.connected:
            self._sendCommand(cmd)

    ##  Set the error state with a message.
    #   \param error String with the error message.
    def _setErrorState(self, error):
        self._updateJobState("error")
        self._error_state = error
        self.onError.emit()

    ##  Request the current scene to be sent to a USB-connected printer.
    #
    #   \param nodes A collection of scene nodes to send. This is ignored.
    #   \param file_name \type{string} A suggestion for a file name to write.
    #   This is ignored.
    #   \param filter_by_machine Whether to filter MIME types by machine. This
    #   is ignored.
    #   \param kwargs Keyword arguments.
    def requestWrite(self, nodes, file_name = None, filter_by_machine = False, file_handler = None, **kwargs):
        if self._global_stack.getProperty("machine_gcode_flavor", "value") == "UltiGCode":
            self._error_message = Message(catalog.i18nc("@info:status", "This printer does not support USB printing because it uses UltiGCode flavor."))
            self._error_message.show()
            return
        elif not self._global_stack.getMetaDataEntry("supports_usb_connection"):
            self._error_message = Message(catalog.i18nc("@info:status", "Unable to start a new job because the printer does not support usb printing."))
            self._error_message.show()
            return

        Application.getInstance().showPrintMonitor.emit(True)
        self.startPrint()

    def _setEndstopState(self, endstop_key, value):
        if endstop_key == b"x_min":
            if self._x_min_endstop_pressed != value:
                self.endstopStateChanged.emit("x_min", value)
            self._x_min_endstop_pressed = value
        elif endstop_key == b"y_min":
            if self._y_min_endstop_pressed != value:
                self.endstopStateChanged.emit("y_min", value)
            self._y_min_endstop_pressed = value
        elif endstop_key == b"z_min":
            if self._z_min_endstop_pressed != value:
                self.endstopStateChanged.emit("z_min", value)
            self._z_min_endstop_pressed = value

    ##  Listen thread function.
    def _listen(self):
        Logger.log("i", "Printer connection listen thread started for %s" % self._serial_port)
        temperature_request_timeout = time.time()
        ok_timeout = time.time()
        while self._connection_state == ConnectionState.connected:
            line = self._readline()
            if self._firmware_version is None and FirmwareVersion.isVersion(line.decode("utf-8")):
                self._firmware_version = FirmwareVersion(line.decode("utf-8").split("\n")[0])
                self.firmwareChange.emit()
            # if not self._version_command_sent and self._firmware_version is None:
            #     self._sendCommand("M115")
            #     self._version_command_sent = True
            # if self._version_command_sent and self._firmware_version is None:
            #     self._getFirmwareVersion(line)

            if line is None:
                break  # None is only returned when something went wrong. Stop listening

            if time.time() > temperature_request_timeout:
                # if self._num_extruders > 1:
                #     self._temperature_requested_extruder_index = (self._temperature_requested_extruder_index + 1) % self._num_extruders
                #     self.sendCommand("M105 T%d" % (self._temperature_requested_extruder_index))
                # else:
                self.sendCommand("M105")
                temperature_request_timeout = time.time() + 5

            if line.startswith(b"Error:"):
                # Oh YEAH, consistency.
                # Marlin reports a MIN/MAX temp error as "Error:x\n: Extruder switched off. MAXTEMP triggered !\n"
                # But a bed temp error is reported as "Error: Temperature heated bed switched off. MAXTEMP triggered !!"
                # So we can have an extra newline in the most common case. Awesome work people.
                if re.match(b"Error:[0-9]\n", line):
                    line = line.rstrip() + self._readline()

                # Skip the communication errors, as those get corrected.
                if b"Extruder switched off" in line or b"Temperature heated bed switched off" in line or b"Something is wrong, please turn off the printer." in line:
                    if not self.hasError():
                        self._setErrorState(line[6:])

            elif b" T:" in line or line.startswith(b"T:"):  # Temperature message
                try:
                    for i in range(0, self._num_extruders):
                        regex = "T" + str(i) + ": *([0-9\.]*)"
                        self._setHotendTemperature(i, float(re.search(regex.encode("UTF-8"), line).group(1)))
                except:
                    pass
                if b"B:" in line:  # Check if it's a bed temperature
                    try:
                        self._setBedTemperature(float(re.search(b"B: *([0-9\.]*)", line).group(1)))
                    except Exception as e:
                        pass
                        #TODO: temperature changed callback
            elif b"_min" in line or b"_max" in line:
                tag, value = line.split(b":", 1)
                self._setEndstopState(tag,(b"H" in value or b"TRIGGERED" in value))

            if self._is_printing:
                if line == b"" and time.time() > ok_timeout:
                    line = b"ok"  # Force a timeout (basically, send next command)

                if b"ok" in line:
                    ok_timeout = time.time() + 5
                    if not self._command_queue.empty():
                        self._sendCommand(self._command_queue.get())
                    elif self._is_paused:
                        line = b""  # Force getting temperature as keep alive
                    else:
                        self._sendNextGcodeLine()
                elif b"resend" in line.lower() or b"rs" in line:  # Because a resend can be asked with "resend" and "rs"
                    try:
                        self._gcode_position = int(line.replace(b"N:",b" ").replace(b"N",b" ").replace(b":",b" ").split()[-1])
                    except:
                        if b"rs" in line:
                            self._gcode_position = int(line.split()[1])

                            # Request the temperature on comm timeout (every 2 seconds) when we are not printing.)
                            # if line == b"":
                            #     # if self._num_extruders > 1:
                            #     #     self._temperature_requested_extruder_index = (self._temperature_requested_extruder_index + 1) % self._num_extruders
                            #     #     self.sendCommand("M105 T%d" % self._temperature_requested_extruder_index)
                            #     # else:
                            #     self.sendCommand("M105")

        Logger.log("i", "Printer connection listen thread stopped for %s" % self._serial_port)

    ##  Send next Gcode in the gcode list
    def _sendNextGcodeLine(self):
        if self._gcode_position >= len(self._gcode):
            return
        if self._gcode_position == 100:
            self._print_start_time_100 = time.time()
        line = self._gcode[self._gcode_position]

        if ";" in line:
            line = line[:line.find(";")]
        line = line.strip()

        # Don't send empty lines. But we do have to send something, so send
        # m105 instead.
        # Don't send the M0 or M1 to the machine, as M0 and M1 are handled as
        # an LCD menu pause.
        if line == "" or line == "M0" or line == "M1":
            line = "M105"
        try:
            if ("G0" in line or "G1" in line) and "Z" in line:
                z = float(re.search("Z([0-9\.]*)", line).group(1))
                if self._current_z != z:
                    self._current_z = z
        except Exception as e:
            Logger.log("e", "Unexpected error with printer connection, could not parse current Z: %s: %s" % (e, line))
            self._setErrorState("Unexpected error: %s" %e)
        checksum = functools.reduce(lambda x,y: x^y, map(ord, "N%d%s" % (self._gcode_position, line)))

        self._sendCommand("N%d%s*%d" % (self._gcode_position, line, checksum))
        self._gcode_position += 1
        self.setProgress((self._gcode_position / len(self._gcode)) * 100)
        self.progressChanged.emit()

    ##  Set the state of the print.
    #   Sent from the print monitor
    def _setJobState(self, job_state):
        if job_state == "pause":
            self._is_paused = True
            self._updateJobState("paused")
        elif job_state == "print":
            self._is_paused = False
            self._updateJobState("printing")
        elif job_state == "abort":
            self.cancelPrint()

    ##  Set the progress of the print.
    #   It will be normalized (based on max_progress) to range 0 - 100
    def setProgress(self, progress, max_progress = 100):
        self._progress = (progress / max_progress) * 100  # Convert to scale of 0-100
        if self._progress == 100:
            # Printing is done, reset progress
            self._gcode_position = 0
            self.setProgress(0)
            self._is_printing = False
            self._is_paused = False
            self._updateJobState("ready")
        self.progressChanged.emit()

    ##  Cancel the current print. Printer connection wil continue to listen.
    def cancelPrint(self):
        self._gcode_position = 0
        self.setProgress(0)
        self._gcode = []

        # Turn off temperatures, fan and steppers
        self._sendCommand("M104 S0 T0")
        self._sendCommand("M104 S0 T1")
        self._sendCommand("M140 S0")
        self._sendCommand("M107")
        self._sendCommand("G91")
        self._sendCommand("G1 Z+0.5 E-5 Y+10 F12000")
        self.homeHead()
        self._sendCommand("M84")
        self._sendCommand("G90")
        self._is_printing = False
        self._is_paused = False
        self._updateJobState("ready")
        Application.getInstance().showPrintMonitor.emit(False)

    ##  Check if the process did not encounter an error yet.
    def hasError(self):
        return self._error_state is not None

    ##  private read line used by printer connection to listen for data on serial port.
    def _readline(self):
        if self._serial is None:
            return None
        try:
            ret = self._serial.readline()
        except Exception as e:
            Logger.log("e", "Unexpected error while reading serial port. %s" % e)
            self._setErrorState("Printer has been disconnected")
            self.close()
            return None
        return ret

    ##  Create a list of baud rates at which we can communicate.
    #   \return list of int
    def _getBaudrateList(self):
        ret = [57600, 115200, 250000, 230400, 38400, 19200, 9600]
        return ret

    def _onFirmwareUpdateComplete(self):
        self._update_firmware_thread.join()
        self._update_firmware_thread = threading.Thread(target = self._updateFirmware)
        self._update_firmware_thread.daemon = True

        self.connect()

    ##  Pre-heats the heated bed of the printer, if it has one.
    #
    #   \param temperature The temperature to heat the bed to, in degrees
    #   Celsius.
    #   \param duration How long the bed should stay warm, in seconds. This is
    #   ignored because there is no g-code to set this.
    @pyqtSlot(float, float)
    def preheatBed(self, temperature, duration):
        Logger.log("i", "Pre-heating the bed to %i degrees.", temperature)
        self._setTargetBedTemperature(temperature)
        self._preheat_bed_timer.start(duration*1000)
        self.preheatBedRemainingTimeChanged.emit()

    ##  Cancels pre-heating the heated bed of the printer.
    #
    #   If the bed is not pre-heated, nothing happens.
    @pyqtSlot()
    def cancelPreheatBed(self):
        Logger.log("i", "Cancelling pre-heating of the bed.")
        self._setTargetBedTemperature(0)
        self._preheat_bed_timer.stop()
        self.preheatBedRemainingTimeChanged.emit()
