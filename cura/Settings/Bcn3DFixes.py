import re

from cura.Settings import GCodeUtils

from UM.Application import Application
from UM.Job import Job
from UM.Logger import Logger

from cura.Settings.ExtruderManager import ExtruderManager


class Bcn3DFixes(Job):
    def __init__(self, container, gcode_list):
        super().__init__()
        self._container = container
        self._gcode_list = gcode_list
        
        if len(ExtruderManager.getInstance().getExtruderStacks()) == 2:
            extruder_left = ExtruderManager.getInstance().getExtruderStack(0)
            extruder_right = ExtruderManager.getInstance().getExtruderStack(1)
        else:
            extruder_left = ExtruderManager.getInstance().getExtruderStack(0)
            extruder_right = extruder_left
        active_extruder = ExtruderManager.getInstance().getActiveExtruderStack()

        # self._activeExtruders = active_extruder.getProperty("active_extruders", "value")
        # self._fixFirstRetract = active_extruder.getProperty("fix_first_retract", "value")
        # self._fixTemperatureOscilation = active_extruder.getProperty("fix_temperature_oscilation", "value")
        self._nozzleSize = [extruder_left.getProperty("machine_nozzle_size", "value"), extruder_right.getProperty("machine_nozzle_size", "value")]

        self._fixToolChangeTravel = active_extruder.getProperty("fix_tool_change_travel", "value")
        self._layerHeight = active_extruder.getProperty("layer_height", "value")
        self._retractionHopHeightAfterExtruderSwitch = [extruder_left.getProperty("retraction_hop_height_after_extruder_switch", "value"),
                                                        extruder_right.getProperty("retraction_hop_height_after_extruder_switch", "value")]
        self._retractionHop = [extruder_left.getProperty("retraction_hop", "value"),
                               extruder_right.getProperty("retraction_hop", "value")]
        self._avoidGrindingFilament = [extruder_left.getProperty("avoid_grinding_filament", "value"),
                                       extruder_right.getProperty("avoid_grinding_filament", "value")]
        self._maxRetracts = [extruder_left.getProperty("retraction_count_max_avoid_grinding_filament", "value"),
                             extruder_right.getProperty("retraction_count_max_avoid_grinding_filament", "value")]
        self._retractionExtrusionWindow = [extruder_left.getProperty("retraction_extrusion_window", "value"),
                                           extruder_right.getProperty("retraction_extrusion_window", "value")]
        self._retractionAmount = [extruder_left.getProperty("retraction_amount", "value"),
                                  extruder_right.getProperty("retraction_amount", "value")]
        self._ZHopAtLayerChange = [extruder_left.getProperty("hop_at_layer_change", "value"),
                                   extruder_right.getProperty("hop_at_layer_change", "value")]
        self._ZHopHeightAtLayerChange = [extruder_left.getProperty("retraction_hop_height_at_layer_change", "value"),
                                         extruder_right.getProperty("retraction_hop_height_at_layer_change", "value")]
        self._ZHopAfterPrimeTower = [extruder_left.getProperty("retraction_hop_after_prime_tower", "value"),
                                     extruder_right.getProperty("retraction_hop_after_prime_tower", "value")]
        self._primeTowerEnabled = active_extruder.getProperty("prime_tower_enable", "value")
        self._CoolLiftHead = [extruder_left.getProperty("cool_lift_head", "value"),
                              extruder_right.getProperty("cool_lift_head", "value")]
        self._purgeBeforeStart = [extruder_left.getProperty("purge_in_bucket_before_start", "value"),
                                  extruder_right.getProperty("purge_in_bucket_before_start", "value")]
        # self._startPurgeDistance = [extruder_left.getProperty("start_purge_distance", "value"),
        #                             extruder_right.getProperty("start_purge_distance", "value")]
        # self._retractReduction = active_extruder.getProperty("retract_reduction", "value")
        # self._switchExtruderRetractionAmount = [extruder_left.getProperty("switch_extruder_retraction_amount", "value"),
        #                                         extruder_right.getProperty("switch_extruder_retraction_amount", "value")]
        # self._machineMinCoolHeatTimeWindow = [extruder_left.getProperty("machine_min_cool_heat_time_window", "value"),
        #                                          extruder_right.getProperty("machine_min_cool_heat_time_window", "value")]
        
        # Temperatures
        self._materialStandByTemperature = [extruder_left.getProperty("material_standby_temperature", "value"),
                                            extruder_right.getProperty("material_standby_temperature", "value")]
        self._materialPrintTemperatureLayer0 = [extruder_left.getProperty("material_print_temperature_layer_0", "value"),
                                                 extruder_right.getProperty("material_print_temperature_layer_0", "value")]
        # self._materialInitialPrintTemperature = [extruder_left.getProperty("material_initial_print_temperature", "value"),
        #                                          extruder_right.getProperty("material_initial_print_temperature", "value")]
        # self._materialFinalPrintTemperature = [extruder_left.getProperty("material_final_print_temperature", "value"),
        #                                         extruder_right.getProperty("material_final_print_temperature", "value")]
        # self._materialPrintTemperature = [extruder_left.getProperty("material_print_temperature", "value"),
        #                                   extruder_right.getProperty("material_print_temperature", "value")]
        # self._materialFlowDependentTemperature = [extruder_left.getProperty("material_flow_dependent_temperature", "value"),
        #                                          extruder_right.getProperty("material_flow_dependent_temperature", "value")]
        
        # Speeds
        self._travelSpeed = [str(int(extruder_left.getProperty("speed_travel", "value") * 60)),
                             str(int(extruder_right.getProperty("speed_travel", "value") * 60))]
        self._retractionRetractSpeed = [str(int(extruder_left.getProperty("retraction_retract_speed", "value") * 60)),
                                        str(int(extruder_right.getProperty("retraction_retract_speed", "value") * 60))]
        self._retractionPrimeSpeed = [str(int(extruder_left.getProperty("retraction_prime_speed", "value") * 60)),
                                      str(int(extruder_right.getProperty("retraction_prime_speed", "value") * 60))]
        self._accelerationEnabled = [extruder_left.getProperty("acceleration_enabled", "value"),
                                     extruder_right.getProperty("acceleration_enabled", "value")]
        self._jerkEnabled = [extruder_left.getProperty("jerk_enabled", "value"),
                             extruder_right.getProperty("jerk_enabled", "value")]
        # self._switchExtruderRetractionSpeed = [str(int(extruder_left.getProperty("switch_extruder_retraction_speed", "value") * 60)),
        #                                        str(int(extruder_right.getProperty("switch_extruder_retraction_speed", "value") * 60))]
        # self._switchExtruderPrimeSpeed = [str(int(extruder_left.getProperty("switch_extruder_prime_speed", "value") * 60)),
        #                                   str(int(extruder_right.getProperty("switch_extruder_prime_speed", "value") * 60))]

        # Dual
        self._smartPurge = [extruder_left.getProperty("smart_purge", "value"),
                            extruder_right.getProperty("smart_purge", "value")]
        self._purgeSpeed = [str(int(extruder_left.getProperty("purge_speed", "value") * 60)),
                            str(int(extruder_right.getProperty("purge_speed", "value") * 60))]
        self._smartPurgePParameter = [extruder_left.getProperty("smart_purge_minimum_purge_distance", "value"),
                                      extruder_right.getProperty("smart_purge_minimum_purge_distance", "value")]
        # self._smartPurgeSParameter = [extruder_left.getProperty("smart_purge_slope", "value"),
        #                               extruder_right.getProperty("smart_purge_slope", "value")]
        # self._smartPurgeEParameter = [extruder_left.getProperty("smart_purge_maximum_purge_distance", "value"),
        #                               extruder_right.getProperty("smart_purge_maximum_purge_distance", "value")]
        
        self._startGcodeInfo = [";BCN3D Fixes applied"] if len(ExtruderManager.getInstance().getExtruderStacks()) <= 2 else [";Warning! - BCN3D Fixes applied only with T0 values"]

        self._IDEXPrint = len(ExtruderManager.getInstance().getUsedExtruderStacks()) > 1
        self._MEXPrint =  not self._IDEXPrint and self._container.getProperty("print_mode", "value") == 'regular'
        self._MirrorOrDuplicationPrint = not self._IDEXPrint and self._container.getProperty("print_mode", "value") != 'regular'

        self._message = None
        self.progress.connect(self._onProgress)
        self.finished.connect(self._onFinished)

    def run(self):
        Job.yieldThread()

        self._handleFixStartGcode()
        self._handleFixAccelerationJerkCommands()
        self._handleChangeLiftHeadMovement()
        self._handleFixToolChangeTravel()
        self._handleTemperatureCommandsRightAfterToolChange()
        self._handleAvoidGrindingFilament()
        self._handleZHopAtLayerChange()
        self._handleZHopAfterPrimeTower()

        # self._handleFixTemperatureOscilation() # Changes to proper temperatures if auto temperature is on. Auto temperature is not on and it's an experimental feature, this will be probably solved from the engine perspective. Therefore it's temporary commented

        # Write BCN3DFixes info
        written_info = False
        for index, layer in enumerate(self._gcode_list):
            lines = layer.split("\n")
            for temp_index in range(len(lines)):
                if layer.startswith(";Generated with Cura_SteamEngine ") and lines[temp_index].startswith(";Sigma ProGen"):
                    lines[temp_index] = lines[temp_index] + "\n" + "\n".join(self._startGcodeInfo)
                    written_info = True
            layer = "\n".join(lines)
            self._gcode_list[index] = layer
            if written_info:
                break

        # Get info of used extruders
        if self._MirrorOrDuplicationPrint:
            extrudersUsed = ";Extruders used: T0 "+str(self._nozzleSize[0])+" T1 "+str(self._nozzleSize[0])
        else:
            if self._MEXPrint:
                countingForTool = int(ExtruderManager.getInstance().getUsedExtruderStacks()[0].getMetaData()['position'])
                if countingForTool == 0:
                    extrudersUsed = ";Extruders used: T0 "+str(self._nozzleSize[0])
                else:
                    extrudersUsed = ";Extruders used: T1 "+str(self._nozzleSize[1])
            else:
                extrudersUsed = ";Extruders used: T0 "+str(self._nozzleSize[0])+" T1 "+str(self._nozzleSize[1])

        self._gcode_list[0] += extrudersUsed+"\n;BCN3D_FIXES\n"
        scene = Application.getInstance().getController().getScene()
        setattr(scene, "gcode_list", self._gcode_list)
        self.setResult(self._gcode_list)

    def _handleFixStartGcode(self):
        '''
            Default behavior:
                Hotends are heated up at print start.
                If one hotend takes more than cooldown window to start printing (usual scenario in DUAL prints) then it will be heated up to Standby temperature.
                -> [Fix 1] if Purge at Start is enabled the Hotend must be heated up to layer 0 temperature 

                Mirror/Duplication prints are internally taken as single extruder prints.
                Cura only heats up left hotend
                -> [Fix 2] Must be added the t1 heat up command 

                In Dual prints there may be some cases where hotends are heated up to printing temperature
                -> [Fix 3] Must be heated up to layer 0 temperature instead 
        '''
        # Fix 1: first temperature. Change standby to start if Purge Before Start enabled
        if self._IDEXPrint:
            countingForTool = 0
            startTemperatures = self._materialPrintTemperatureLayer0[:]
            for index, layer in enumerate(self._gcode_list):
                lines = layer.split("\n")
                if not layer.startswith(";LAYER:"):
                    temp_index = 0
                    while temp_index < len(lines):
                        line = lines[temp_index]
                        if line.startswith("T0") or line.startswith("T1"):
                            if "T0" in line:
                                countingForTool = 0
                            else:
                                countingForTool = 1
                        if line.startswith("M104 S") or line.startswith("M109 S"):
                            if self._purgeBeforeStart[countingForTool]:
                                startTemperatures[countingForTool] = GCodeUtils.getValue(line, "S")
                                lines[temp_index] = "M104 S"+str(self._materialPrintTemperatureLayer0[countingForTool]) if line.startswith("M104 S") else "M109 S"+str(self._materialPrintTemperatureLayer0[countingForTool])
                        elif line.startswith("M104 T") or line.startswith("M109 T"):
                            toolNumber = int(GCodeUtils.getValue(line, "T"))
                            if self._purgeBeforeStart[toolNumber]:
                                startTemperatures[toolNumber] = GCodeUtils.getValue(line, "S")
                                lines[temp_index] = "M104 T" + str(toolNumber) + " S"+str(self._materialPrintTemperatureLayer0[toolNumber]) if line.startswith("M104 T") else "M109 T" + str(toolNumber) + " S" + str(self._materialPrintTemperatureLayer0[toolNumber])
                        temp_index += 1
                    layer = "\n".join(lines)
                    self._gcode_list[index] = layer
                else:
                    break
            Logger.log("d", "fix_start_gcode applied")
        # Fix 2: temperatures for Mirror/Duplication print modes
        if self._MirrorOrDuplicationPrint:
            self._startGcodeInfo.append("; - Fix start GCode")
            startGcodeCorrected = False
            for index, layer in enumerate(self._gcode_list):
                lines = layer.split("\n")
                temp_index = 0
                while temp_index < len(lines):
                    try:
                        line = lines[temp_index]
                        if line.startswith("M104 S"+str(self._materialPrintTemperatureLayer0[0])):
                            lines[temp_index] += "\nM104 T1 S"+str(self._materialPrintTemperatureLayer0[0])+" ;Fixed T1 temperature"
                        if line.startswith("M109 S"+str(self._materialPrintTemperatureLayer0[0])):
                            lines[temp_index] += "\nM109 T1 S"+str(self._materialPrintTemperatureLayer0[0])+" ;Fixed T1 temperature"
                            startGcodeCorrected = True
                            break
                        temp_index += 1
                    except:
                        break
                layer = "\n".join(lines)
                self._gcode_list[index] = layer
                if startGcodeCorrected:
                    break
            Logger.log("d", "fix_start_gcode applied")
        # Fix 3: temperatures for DUAL extruder prints
        elif self._IDEXPrint:
            self._startGcodeInfo.append("; - Fix start GCode")
            startGcodeCorrected = False
            for index, layer in enumerate(self._gcode_list):
                lines = layer.split("\n")
                temp_index = 0
                while temp_index < len(lines):
                    try:
                        line = lines[temp_index]
                        if line.startswith("M104 S"+str(self._materialPrintTemperatureLayer0[0])):
                            lines[temp_index] = "M104 T0 S"+str(self._materialPrintTemperatureLayer0[0])+" ;Fixed T0 temperature"
                        if line.startswith("M109 S"+str(self._materialPrintTemperatureLayer0[0])):
                            lines[temp_index] = "M109 T0 S"+str(self._materialPrintTemperatureLayer0[0])+" ;Fixed T0 temperature"
                            startGcodeCorrected = True
                            break
                        temp_index += 1
                    except:
                        break
                layer = "\n".join(lines)
                self._gcode_list[index] = layer
                if startGcodeCorrected:
                    break
            Logger.log("d", "fix_start_gcode applied")

    def _handleFixToolChangeTravel(self):
        '''
            Default behavior:
                When changing tools, the new tool will go straight to the last position of the first tool.
                Then move to the position it actually has to print.
                -> [Fix 1] Proper movement is make the new tool to go straight to the place it has to print and avoid unnecessary travels 
                
                In random places there's a travel to (layer_start_x, layer_start_y)
                -> [Fix 2] Remove this travel
        '''
        # Fix 1: Allows the new tool to go straight to the position where it has to print, instead of going to the last position before tool change and then travel to the position where it has to print
        if self._fixToolChangeTravel and self._IDEXPrint:
            self._startGcodeInfo.append("; - Fix Tool Change Travel")
            for index, layer in enumerate(self._gcode_list):
                lines = layer.split("\n")
                temp_index = 0
                while temp_index < len(lines):
                    try:
                        line = lines[temp_index]
                        lineCount = 1
                        if line.startswith("T0") or line.startswith("T1"):
                            if "T0" in line:
                                countingForTool = 0
                            else:
                                countingForTool = 1
                            while not lines[temp_index + lineCount].startswith(";TYPE"):
                                line = lines[temp_index + lineCount]
                                if GCodeUtils.charsInLine(["G0", "X", "Y"], line):
                                    if GCodeUtils.charsInLine(["Z"], line):
                                        zValue = GCodeUtils.getValue(line, "Z")
                                    xValue = GCodeUtils.getValue(line, "X")
                                    yValue = GCodeUtils.getValue(line, "Y")
                                    del lines[temp_index + lineCount]
                                    lineCount -= 1
                                lineCount += 1
                            lines[temp_index + lineCount] += "\nG0 F" + self._travelSpeed[countingForTool] + " X" + str(xValue) + " Y" + str(yValue) + "\nG0 Z" + str(zValue) + " ;Fixed travel after tool change"
                            break
                        temp_index += lineCount
                    except:
                        break
                layer = "\n".join(lines)
                # Fix 2: Fix strange travel to X105 Y297
                regex = r"\n.*X" + str(int(self._container.getProperty("layer_start_x", "value"))) + " Y" + str(int(self._container.getProperty("layer_start_y", "value"))) + ".*"
                layer = re.sub(regex, "", layer)
                self._gcode_list[index] = layer
            Logger.log("d", "fix_tool_change_travel applied")

    def _handleTemperatureCommandsRightAfterToolChange(self):
        '''
            Default behavior:
                M104 Sends temperature command
                M109 Sends temperature command + forces the machine to wait until the temperature has been reached
                When changing tools, the machine comes from an M104, then inserts Extruder GCode (may include purge commands), then sends the M109, and then bak to the part.
                -> [Fix 1] Send the M109 before the Extruder GCode
        '''        
        # Fix 1: Places M109 temperature commands right after toolchange, before Extruder gcode is executed, to improve all purge commands and machine reliability
        if self._IDEXPrint:
            self._startGcodeInfo.append("; - Temperature Commands Right After Tool Change")
            for index, layer in enumerate(self._gcode_list):
                if layer.startswith(";LAYER:"):
                    lines = layer.split("\n")
                    temp_index = 0
                    while temp_index < len(lines):
                        try:
                            line = lines[temp_index]
                            lineCount = 1
                            if line.startswith("T0") or line.startswith("T1"):
                                if "T0" in line:
                                    countingForTool = 0
                                else:
                                    countingForTool = 1
                                while not lines[temp_index + lineCount].startswith(";TYPE"):
                                    lineWithTemperatureCommand = lines[temp_index + lineCount]
                                    if GCodeUtils.charsInLine(["M109 S"], lineWithTemperatureCommand):
                                        lines[temp_index] += '\nM109 S'+str(GCodeUtils.getValue(lineWithTemperatureCommand, "S"))
                                        del lines[temp_index + lineCount]
                                        lineCount -= 1
                                        break
                                    lineCount += 1
                            temp_index += lineCount
                        except:
                            break
                    layer = "\n".join(lines)
                    self._gcode_list[index] = layer
            Logger.log("d", "_handleTemperatureCommandsRightAfterToolChange() applied")            

    def _handleAvoidGrindingFilament(self):
        '''
            Custom feature to bring the hotend to the purge bucket and purge the desired amount if there has been X retractions in Y distance of filament. Then continue printing with renewed filament.
        '''
        if self._avoidGrindingFilament[0] or self._avoidGrindingFilament[1]:
            self._startGcodeInfo.append("; - Prevent Filament Grinding")
            retractionsPerExtruder = [[], []]
            countingForTool = 0
            purgedOffset = [0, 0]
            printArea = ''
            for index, layer in enumerate(self._gcode_list):
                lines = layer.split("\n")
                temp_index = 0
                if layer.startswith(";LAYER:"):
                    while temp_index < len(lines):
                        line = lines[temp_index]
                        if line.startswith("T0"):
                            countingForTool = 0
                            if not (layer.startswith(";LAYER:0") or layer.startswith(";LAYER:-")) and self._smartPurge[countingForTool]:
                                purgedOffset[countingForTool] += self._smartPurgePParameter[countingForTool]
                        elif line.startswith("T1"):
                            countingForTool = 1
                            if not (layer.startswith(";LAYER:0") or layer.startswith(";LAYER:-")) and self._smartPurge[countingForTool]:
                                purgedOffset[countingForTool] += self._smartPurgePParameter[countingForTool]
                        elif line.startswith(';TYPE:'):
                            printArea = line
                        elif " E" in line and "G92" not in line:
                            eValue = GCodeUtils.getValue(line, "E")
                            lineCount = temp_index - 1
                            try:
                                if not lines[temp_index + 1].startswith("G92"):
                                    while lineCount >= 0:
                                        line = lines[lineCount]
                                        if " E" in line and "G92" not in line:
                                            if eValue < GCodeUtils.getValue(line, "E") and self._avoidGrindingFilament[countingForTool]:
                                                purgeLength = self._retractionExtrusionWindow[countingForTool]
                                                retractionsPerExtruder[countingForTool].append(eValue)
                                                if len(retractionsPerExtruder[countingForTool]) > self._maxRetracts[countingForTool]:
                                                    if (retractionsPerExtruder[countingForTool][-1] - retractionsPerExtruder[countingForTool][0]) < purgeLength + purgedOffset[countingForTool]:
                                                        if printArea != ';TYPE:WALL-OUTER':
                                                            # Delete extra travels
                                                            while GCodeUtils.charsInLine(["G0", "X", "Y"], lines[temp_index + 1]):
                                                                xPosition = GCodeUtils.getValue(lines[temp_index + 1], "X")
                                                                yPosition = GCodeUtils.getValue(lines[temp_index + 1], "Y")
                                                                del lines[temp_index + 1]
                                                            # Add purge commands
                                                            lines[temp_index] += "\n;prevent filament grinding on T" + str(countingForTool) + \
                                                                                "\nG1 F" + self._travelSpeed[countingForTool] + \
                                                                                "\nG71" + \
                                                                                "\nG91" + \
                                                                                "\nG1 F" + self._travelSpeed[countingForTool] + " Z" + str(self._retractionHopHeightAfterExtruderSwitch[countingForTool]) + \
                                                                                "\nG90" + \
                                                                                "\nG1 F" + self._retractionPrimeSpeed[countingForTool] + " E" + str(round(eValue + self._retractionAmount[countingForTool], 5)) + \
                                                                                "\nG1 F" + self._purgeSpeed[countingForTool] + " E" + str(round(eValue + self._retractionAmount[countingForTool] + purgeLength,5)) + \
                                                                                "\nG1 F" + self._retractionRetractSpeed[countingForTool] + " E" + str(round(eValue + purgeLength, 5)) + \
                                                                                "\nG4 P2000" + \
                                                                                "\nG92 E" + str(eValue) + \
                                                                                "\nG1 F" + self._travelSpeed[countingForTool] + \
                                                                                "\nG72" + \
                                                                                "\nG1 F" + self._travelSpeed[countingForTool] + " X" + str(xPosition)+" Y" + str(yPosition) + \
                                                                                "\nG91" + \
                                                                                "\nG1 F" + self._travelSpeed[countingForTool] + " Z-" + str(self._retractionHopHeightAfterExtruderSwitch[countingForTool]) + \
                                                                                "\nG90" + \
                                                                                "\n;end of the filament grinding prevention protocol"
                                                            retractionsPerExtruder[countingForTool] = []
                                                            purgedOffset[countingForTool] = 0
                                                    else:
                                                        del retractionsPerExtruder[countingForTool][0]
                                            break
                                        elif line.startswith("T") or line.startswith("G92"):
                                            break
                                        lineCount -= 1
                            except:
                                break
                        temp_index += 1
                layer = "\n".join(lines)
                self._gcode_list[index] = layer
            Logger.log("d", "avoid_grinding_filament applied")

    def _handleZHopAtLayerChange(self):
        '''
            Custom feature to add a Z Hop (+retraction) at layer change
        '''
        if self._ZHopAtLayerChange[0] or self._ZHopAtLayerChange[1]:
            self._startGcodeInfo.append("; - Z Hop At Layer Change")
            countingForTool = 0
            for index, layer in enumerate(self._gcode_list):
                lines = layer.split("\n")
                temp_index = 0
                while temp_index < len(lines):
                    line = lines[temp_index]
                    temp_index_2 = 1
                    if self._ZHopAtLayerChange[countingForTool] and line.startswith(";LAYER:") and not (line.startswith(";LAYER:0") or line.startswith(";LAYER:-")):
                        if not line.startswith(";LAYER:1") or self._container.getProperty("print_mode", "value") == "regular":
                            lines[temp_index] += "\nG91" + \
                                                 "\nG1 F" + self._retractionRetractSpeed[countingForTool] + " E-" + str(round(self._retractionAmount[countingForTool], 5)) + \
                                                 "\nG1 F" + self._travelSpeed[countingForTool] + " Z" + str(round(self._layerHeight + self._ZHopHeightAtLayerChange[countingForTool], 5)) + " ;z hop at layer change" + \
                                                 "\nG90"
                            while not GCodeUtils.charsInLine(["E"], lines[temp_index + temp_index_2]):
                                temp_index_2 += 1
                            lines[temp_index + temp_index_2] += "\nG91" + \
                                                                "\nG1 F" + self._retractionRetractSpeed[countingForTool] + " E" + str(round(self._retractionAmount[countingForTool], 5)) + \
                                                            "\nG90"
                    elif line.startswith("T0"):
                        countingForTool = 0
                    elif line.startswith("T1"):
                        countingForTool = 1
                    temp_index += temp_index_2
                layer = "\n".join(lines)
                self._gcode_list[index] = layer
            Logger.log("d", "hop_at_layer_change applied")

    def _handleChangeLiftHeadMovement(self):
        '''
            Default behavior:
                when the lift head setting is enabled it moves in X+Z, then waits, then X+Z
                -> [Fix] move X, then Z, then waits,  then X, then Z
        '''
        if self._CoolLiftHead[0] or self._CoolLiftHead[1]:
            self._startGcodeInfo.append("; - Change Lift Head Movement")
            fixMovementInNextLayer = False
            countingForTool = 0
            for index, layer in enumerate(self._gcode_list):
                # Fix movement coming back to the part
                lines = layer.split("\n")
                if fixMovementInNextLayer:
                    temp_index = 0
                    while temp_index < len(lines):
                        line = lines[temp_index]
                        if GCodeUtils.charsInLine(["G0", "X", "Y", "Z"], line):
                            zValue = GCodeUtils.getValue(line, "Z")
                            lines[temp_index] = line.split("Z")[0] + "\nG0 Z"+str(zValue)+' ;fixed movement coming back to the part'
                            break
                        temp_index += 1
                # fix movement leaving the part
                if ';Small layer, adding delay' in layer:
                    temp_index = 0
                    while temp_index < len(lines):
                        line = lines[temp_index]
                        if ';Small layer, adding delay' in line:
                            temp_index_2 = temp_index + 1
                            while temp_index_2 < len(lines):
                                if "Z" in lines[temp_index_2]:
                                    zValue = GCodeUtils.getValue(lines[temp_index_2], "Z")
                                    fValue = GCodeUtils.getValue(lines[temp_index_2], "F")
                                    xValue = GCodeUtils.getValue(lines[temp_index_2 + 1], "X")
                                    yValue = GCodeUtils.getValue(lines[temp_index_2 + 1], "Y")
                                    lines[temp_index_2 + 1] = "G0" + str(" F" + str(fValue) if fValue else "") + " X" + str(xValue) + " Y" + str(yValue) + \
                                                              "\nG0 Z" + str(zValue) + ' ;fixed movement leaving the part'
                                    del lines[temp_index_2]
                                    temp_index_2 -= 1
                                    break
                                temp_index_2 += 1
                        temp_index += 1
                    fixMovementInNextLayer = True
                layer = "\n".join(lines)
                self._gcode_list[index] = layer
            Logger.log("d", "_handleChangeLiftHeadMovement() applied")

    def _handleZHopAfterPrimeTower(self):
        '''
            Custom feature to add a Z Hop (+retraction) after prime tower
            Note: if it does support after prime tower it will not hop until moving to part!
        '''
        if (self._ZHopAfterPrimeTower[0] or self._ZHopAfterPrimeTower[1]) and self._IDEXPrint and self._primeTowerEnabled:
            self._startGcodeInfo.append("; - Z Hop After Prime Tower")
            countingForTool = 0
            for index, layer in enumerate(self._gcode_list):
                lines = layer.split("\n")
                if layer.startswith(";LAYER:") and not (layer.startswith(";LAYER:0") or layer.startswith(";LAYER:-")):
                    temp_index = 0
                    while temp_index < len(lines):
                        line = lines[temp_index]
                        if line.startswith("T0"):
                            countingForTool = 0
                        elif line.startswith("T1"):
                            countingForTool = 1
                        elif line.startswith(";TYPE:SUPPORT") and self._ZHopAfterPrimeTower[countingForTool]:
                            temp_index_2 = temp_index
                            addHop = False
                            hopFixed = False
                            while temp_index_2 < len(lines) and not hopFixed:
                                line = lines[temp_index_2]
                                if line.startswith(";TYPE:SUPPORT"):
                                    addHop = True
                                elif addHop and ((line.startswith(";TYPE:") and not line.startswith(";TYPE:SUPPORT")) or line.startswith(";TIME_ELAPSED:")):
                                    temp_index_3 = temp_index_2 - 1
                                    while temp_index_3 >= 0:
                                        line = lines[temp_index_3]
                                        if GCodeUtils.charsInLine(["E"], line):
                                            lines[temp_index_3] += "\nG91" + \
                                                                   "\nG1 F" + self._travelSpeed[countingForTool] + " Z" + str(round(self._retractionHop[countingForTool], 5)) + " ;z hop after prime tower" + \
                                                                   "\nG90"
                                            lines[temp_index_2] = "G91" + \
                                                                  "\nG1 F" + self._travelSpeed[countingForTool] + " Z" + str(-round(self._retractionHop[countingForTool], 5)) + " ;z hop after prime tower" + \
                                                                  "\nG90\n" + \
                                                                  lines[temp_index_2]
                                            hopFixed = True
                                            break
                                        temp_index_3 -= 1
                                temp_index_2 += 1
                        temp_index += 1
                layer = "\n".join(lines)
                self._gcode_list[index] = layer
            Logger.log("d", "retraction_hop_after_prime_tower applied")

    def _handleFixAccelerationJerkCommands(self):
        '''
            Removes acceleration/jerk (M204/M205) commands if the acceleration/jerk is already set to that value
        '''
        if self._accelerationEnabled[0] or self._accelerationEnabled[1] or self._jerkEnabled[0] or self._jerkEnabled[1]:
            self._startGcodeInfo.append("; - Fix Acceleration/Jerk commands")
            # remove commands which have no X/Y movement after
            for index, layer in enumerate(self._gcode_list):
                lines = layer.split("\n")
                if layer.startswith(";LAYER:"):
                    temp_index = 0
                    while temp_index < len(lines):
                        line = lines[temp_index]
                        # Fix acceleration
                        if line.startswith("M204 S"):
                            usefulCommand = False
                            temp_index_2 = temp_index + 1
                            while temp_index_2 < len(lines) and not lines[temp_index_2].startswith("M204 S"):
                                if GCodeUtils.charsInLine(["G0", "X", "Y"], lines[temp_index_2]) or GCodeUtils.charsInLine(["G1", "X", "Y"], lines[temp_index_2]):
                                    usefulCommand = True
                                    break
                                temp_index_2 += 1
                            if not usefulCommand:
                                del lines[temp_index]
                                temp_index -= 1
                        # Fix jerk
                        elif line.startswith("M205 X") and GCodeUtils.charsInLine(["Y"], line):
                            usefulCommand = False
                            temp_index_2 = temp_index + 1
                            while temp_index_2 < len(lines) and not lines[temp_index_2].startswith("M204 S"):
                                if GCodeUtils.charsInLine(["G0", "X", "Y"], lines[temp_index_2]) or GCodeUtils.charsInLine(["G1", "X", "Y"], lines[temp_index_2]):
                                    usefulCommand = True
                                    break
                                temp_index_2 += 1
                            if not usefulCommand:
                                del lines[temp_index]
                                temp_index -= 1
                        temp_index += 1
                    layer = "\n".join(lines)
                    self._gcode_list[index] = layer
            # remove commands which imply no acceleration/jerk variations
            acceleration = None
            xJerk, yJerk = None, None
            for index, layer in enumerate(self._gcode_list):
                lines = layer.split("\n")
                if layer.startswith(";LAYER:"):
                    temp_index = 0
                    while temp_index < len(lines):
                        line = lines[temp_index]
                        # Fix acceleration
                        if line.startswith("M204 S"):
                            if acceleration and GCodeUtils.getValue(line, "S") == acceleration:
                                del lines[temp_index]
                                temp_index -= 1
                            else:
                                acceleration = GCodeUtils.getValue(line, "S")
                        elif line.startswith("M205 X") and GCodeUtils.charsInLine(["Y"], line):
                            if xJerk and GCodeUtils.getValue(line, "X") == xJerk and yJerk and  GCodeUtils.getValue(line, "Y") == yJerk:
                                del lines[temp_index]
                                temp_index -= 1
                            else:
                                xJerk = GCodeUtils.getValue(line, "X")
                                yJerk = GCodeUtils.getValue(line, "Y")
                        temp_index += 1
                    layer = "\n".join(lines)
                    self._gcode_list[index] = layer
            Logger.log("d", "_handleFixAccelerationJerkCommands() applied")
    
    # def _handleFixTemperatureOscilation(self):
    #     if self._fixTemperatureOscilation and self._IDEXPrint:
    #         self._startGcodeInfo.append("; - Fix Temperature Oscilation")
    #         # Fix oscilation when using Auto Temperature
    #         if self._materialFlowDependentTemperature[0] or self._materialFlowDependentTemperature[1]:
    #             # Scan all temperatures
    #             temperatures = []  # [(layerIndex, lineIndex, action, line)]
    #             for index, layer in enumerate(self._gcode_list):
    #                 # if index > 2: # avoid altering layer 0
    #                 lines = layer.split("\n")
    #                 temp_index = 0
    #                 while temp_index < len(lines):
    #                     line = lines[temp_index]
    #                     if layer.startswith(";LAYER:"):
    #                         if line.startswith("M109"):
    #                             temperatures.append([index, temp_index, "heat", line])
    #                         elif line.startswith("T"):
    #                             temperatures.append([index, temp_index, "toolChange", line])
    #                         elif line.startswith("M104"):
    #                             if line.startswith("M104 T"):
    #                                 temperatures.append([index, temp_index, "preheat", line])
    #                             else:
    #                                 temperatures.append([index, temp_index, "unknown", line])
    #                     temp_index += 1
    #             # Define "unknown" roles
    #             for elementIndex in range(len(temperatures)):
    #                 action = temperatures[elementIndex][2]
    #                 if action == "unknown":
    #                     if elementIndex + 1 < len(temperatures):
    #                         if temperatures[elementIndex + 1][3].startswith("T"):
    #                             action = "coolDownActive"
    #                         else:
    #                             action = "setpoint"
    #                     temperatures[elementIndex][2] = action
    #                 elif action == "preheat":
    #                     temp_index = elementIndex - 1
    #                     while temp_index >= 0 and temperatures[temp_index][2] != "toolChange":
    #                         if temperatures[temp_index][2] == 'preheat':
    #                             action = "coolDownIdle"
    #                             temperatures[temp_index][2] = action
    #                             break
    #                         temp_index -= 1
    #             # Correct all temperatures
    #             countingForTool = 0
    #             for elementIndex in range(len(temperatures)):
    #                 action = temperatures[elementIndex][2]
    #                 if action == "toolChange":
    #                     if temperatures[elementIndex][3] == "T0":
    #                         countingForTool = 0
    #                     else:
    #                         countingForTool = 1
    #                 temperature_inertia_initial_fix = self._materialInitialPrintTemperature[countingForTool] - self._materialPrintTemperature[countingForTool]
    #                 temperature_inertia_final_fix = self._materialFinalPrintTemperature[countingForTool] - self._materialPrintTemperature[countingForTool]
    #                 if action == "preheat":
    #                     temp_index = elementIndex + 1
    #                     toolChanged = False
    #                     while temp_index < len(temperatures):
    #                         if temperatures[temp_index][2] == "toolChange":
    #                             if toolChanged:
    #                                 break
    #                             else:
    #                                 toolChanged = True
    #                         elif temperatures[temp_index][2] == "heat":
    #                             heatIndex = temp_index
    #                         elif toolChanged and temperatures[temp_index][2] == "setpoint":
    #                             correctTemperatureValue = GCodeUtils.getValue(temperatures[temp_index][3], "S") + temperature_inertia_initial_fix
    #                             temperatures[elementIndex][3] = temperatures[elementIndex][3].split("S")[0] + "S" + str(correctTemperatureValue)
    #                             temperatures[heatIndex][3] = temperatures[heatIndex][3].split("S")[0] + "S" + str(correctTemperatureValue)
    #                             break
    #                         temp_index += 1
    #                 elif action == "coolDownIdle":
    #                     correctTemperatureValue = max(GCodeUtils.getValue(temperatures[elementIndex][3], "S") + temperature_inertia_initial_fix,
    #                         self._materialStandByTemperature[countingForTool])
    #                     temperatures[elementIndex][3] = temperatures[elementIndex][3].split("S")[0] + "S" + str(correctTemperatureValue)
    #                 elif action == "coolDownActive":
    #                     temp_index = elementIndex - 1
    #                     while temp_index >= 0:
    #                         if temperatures[temp_index][2] == "coolDownActive":
    #                             break
    #                         if temperatures[temp_index][2] == "setpoint":
    #                             correctTemperatureValue = GCodeUtils.getValue(temperatures[temp_index][3], "S") + temperature_inertia_final_fix
    #                             temperatures[elementIndex][3] = temperatures[elementIndex][3].split("S")[0] + "S" + str(correctTemperatureValue)
    #                             break
    #                         temp_index -= 1
    #             # Set back new corrected temperatures
    #             for index, layer in enumerate(self._gcode_list):
    #                 lines = layer.split("\n")
    #                 temp_index = 0
    #                 while temp_index < len(lines) and len(temperatures) > 0:
    #                     if index == temperatures[0][0] and temp_index == temperatures[0][1]:
    #                         lines[temp_index] = temperatures[0][3]
    #                         del temperatures[0]
    #                     temp_index += 1
    #                 layer = "\n".join(lines)
    #                 self._gcode_list[index] = layer
    #         # Force standby temperature if it exceeds Minimal Time before first print of this hotend
    #         idleTime = 0
    #         lookingForIdleExtruder = True
    #         applied = False
    #         for index, layer in enumerate(self._gcode_list):
    #             lines = layer.split("\n")
    #             if layer.startswith(";LAYER:"):
    #                 temp_index = 0
    #                 while not applied and temp_index < len(lines):
    #                     # look for the idle extruder at start
    #                     if lookingForIdleExtruder:
    #                         if lines[temp_index].startswith("T1"):
    #                             idleExtruder = 0
    #                             lookingForIdleExtruder = False
    #                         elif GCodeUtils.charsInLine(["G1", "F", "X", "Y", "E"], lines[temp_index]):
    #                             idleExtruder = 1
    #                             lookingForIdleExtruder = False
    #                     # once idle extruder is found, look when it enters
    #                     elif (idleExtruder == 0 and lines[temp_index].startswith("T0")) or (idleExtruder == 1 and lines[temp_index].startswith("T1")):
    #                         # apply fix if needed
    #                         if layer.startswith(";LAYER:0"):
    #                             applied = True
    #                             break
    #                         else:
    #                             idleTime = float(lines[-2].split('TIME_ELAPSED:')[1])
    #                             if self._machineMinCoolHeatTimeWindow[idleExtruder] > 0 and idleTime >= self._machineMinCoolHeatTimeWindow[idleExtruder]:
    #                                 lines[temp_index] = "M109 T"+str(idleExtruder)+" S"+str(self._materialPrintTemperatureLayer0[idleExtruder])+" ;T"+str(idleExtruder)+" set to initial layer temperature\n" + lines[temp_index]
    #                                 applied = True
    #                     temp_index += 1
    #                 if applied:
    #                     if not layer.startswith(";LAYER:0"):
    #                         layer = "\n".join(lines)
    #                         self._gcode_list[index] = layer
    #                     break
    #         if applied and not layer.startswith(";LAYER:0"):
    #             for index, layer in enumerate(self._gcode_list):
    #                 if layer.startswith(";LAYER:"):
    #                     layer = "M104 T"+str(idleExtruder)+" S"+str(self._materialStandByTemperature[idleExtruder])+" ;T"+str(idleExtruder)+" set to standby temperature\n" + layer
    #                     break
    #             self._gcode_list[index] = layer
    #         Logger.log("d", "fix_temperature_oscilation applied")

    def setMessage(self, message):
        self._message = message

    def _onFinished(self, job):
        if self == job and self._message is not None:
            self._message.hide()
            self._message = None

    def _onProgress(self, job, amount):
        if self == job and self._message:
            self._message.setProgress(amount)