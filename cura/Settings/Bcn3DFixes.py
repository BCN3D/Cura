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
        
        extruder_left = ExtruderManager.getInstance().getExtruderStack(0)
        extruder_right = ExtruderManager.getInstance().getExtruderStack(1)
        active_extruder = ExtruderManager.getInstance().getActiveExtruderStack()

        # self._activeExtruders = active_extruder.getProperty("active_extruders", "value")
        # self._fixFirstRetract = active_extruder.getProperty("fix_first_retract", "value")
        # self._fixTemperatureOscilation = active_extruder.getProperty("fix_temperature_oscilation", "value")

        self._fixToolChangeTravel = active_extruder.getProperty("fix_tool_change_travel", "value")
        self._layerHeight = active_extruder.getProperty("layer_height", "value")
        self._retractionHopHeightAfterExtruderSwitch = [extruder_left.getProperty("retraction_hop_height_after_extruder_switch", "value"),
                                                        extruder_right.getProperty("retraction_hop_height_after_extruder_switch", "value")]
        # self._retractionHop = [extruder_left.getProperty("retraction_hop", "value"),
        #                        extruder_right.getProperty("retraction_hop", "value")]
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
        
        self._startGcodeInfo = [";BCN3D Fixes applied"]
        
        self._IDEXPrint = len(ExtruderManager.getInstance().getUsedExtruderStacks()) > 1
        # self._MEXPrint =  not self._IDEXPrint and self._container.getProperty("print_mode", "value") == 'regular'
        self._MirrorOrDuplicationPrint = not self._IDEXPrint and self._container.getProperty("print_mode", "value") != 'regular'

        self._message = None
        self.progress.connect(self._onProgress)
        self.finished.connect(self._onFinished)

    def run(self):
        Job.yieldThread()

        self._handleFixStartGcode()
        self._handleCoolDownToZeroAtEnd()
        self._handleFixToolChangeTravel()
        self._handleAvoidGrindingFilament()
        self._handleZHopAtLayerChange()

        # self._handleActiveExtruders()
        '''
            Not needed anymore:
            - extruders heat as expected
            - for mirror/dupli gcodes are added to the start gcode
            - the same for M108 P1
            - it would be interesting to add purge commands, but used extruders need to be retrieved and also force the value calculation according to used extruders (enable _handleFixFirstRetract in that case)
        '''
        # self._handleFixFirstRetract()          # Not needed if there are no retract commands in the start gcode
        # self._handleFixTemperatureOscilation() # Changes to proper temperatures if auto temperature is on. Auto temperature is not on, so it's not needed
        # self._handleSmartPurge()               # the command is added as parameters in the fdmprinter. Force values to 0 if manually changed but smartpurge is disabled
        # self._handleRetractReduction()         # Useless feature. To be removed

        written_info = False
        # Write Sigma Vitamins info
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

        self._gcode_list[0] += ";BCN3D_FIXES\n"
        scene = Application.getInstance().getController().getScene()
        setattr(scene, "gcode_list", self._gcode_list)
        self.setResult(self._gcode_list)

    def _handleFixStartGcode(self):
        # Fix temperatures for Mirror/Duplication print modes
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

    def _handleCoolDownToZeroAtEnd(self):
        # Change last standby temperature of the file to zero
        if self._IDEXPrint:
            self._startGcodeInfo.append("; - Cool Down To Zero At End")
            cooledDownToZero = False
            self._gcode_list.reverse()
            for index, layer in enumerate(self._gcode_list):
                lines = layer.split("\n")
                lines.reverse()
                temp_index = 0
                while temp_index < len(lines):
                    try:
                        line = lines[temp_index]
                        if GCodeUtils.charsInLine(["M104 T0 S"+str(self._materialStandByTemperature[0])], line) or GCodeUtils.charsInLine(["M104 T1 S"+str(self._materialStandByTemperature[1])], line):
                            if "T1" in line:
                                lines[temp_index] = "M104 T1 S0 ;Standby Temperature set to Zero\n"
                            else:
                                lines[temp_index] = "M104 T0 S0 ;Standby Temperature set to Zero\n"
                            cooledDownToZero = True
                            break
                        temp_index += 1
                    except:
                        break
                if cooledDownToZero:
                    lines.reverse()
                    layer = "\n".join(lines)
                    self._gcode_list[index] = layer
                    break
            self._gcode_list.reverse()
            Logger.log("d", "cool_down_to_zero_at_end applied")

    def _handleFixToolChangeTravel(self):
        # Allows the new tool to go straight to the position where it has to print, instead of going to the last position before tool change and then travel to the position where it has to print
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
                            oldLines = ''
                            while not lines[temp_index + lineCount].startswith(";TYPE"):
                                line = lines[temp_index + lineCount]
                                if GCodeUtils.charsInLine(["G0", "X", "Y"], line):
                                    if GCodeUtils.charsInLine(["Z"], line):
                                        zValue = GCodeUtils.getValue(line, "Z")
                                    xValue = GCodeUtils.getValue(line, "X")
                                    yValue = GCodeUtils.getValue(line, "Y")
                                    oldLines += '\n;removed travel ' + lines[temp_index + lineCount]
                                    del lines[temp_index + lineCount]
                                    lineCount -= 1
                                lineCount += 1
                            lines[temp_index + lineCount] += oldLines + "\nG0 F" + self._travelSpeed[countingForTool] + " X" + str(xValue) + " Y" + str(yValue) + "\nG0 Z" + str(zValue) + " ;Fixed travel after tool change"
                            break
                        temp_index += lineCount
                    except:
                        break
                layer = "\n".join(lines)
                # # Fix strange travel to X105 Y297
                # regex = r"\n.*X" + str(int(self._container.getProperty("layer_start_x", "value"))) + " Y" + str(int(self._container.getProperty("layer_start_y", "value"))) + ".*"
                # layer = re.sub(regex, "", layer)
                self._gcode_list[index] = layer
            Logger.log("d", "fix_tool_change_travel applied")

    def _handleAvoidGrindingFilament(self):
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
                            if not layer.startswith(";LAYER:0") and self._smartPurge[countingForTool]:
                                purgedOffset[countingForTool] += self._smartPurgePParameter[countingForTool]
                        elif line.startswith("T1"):
                            countingForTool = 1
                            if not layer.startswith(";LAYER:0") and self._smartPurge[countingForTool]:
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
                                                            oldLines = ''
                                                            while GCodeUtils.charsInLine(["G0", "X", "Y"], lines[temp_index + 1]):
                                                                oldLines += '\n;removed travel ' + lines[temp_index + 1]
                                                                xPosition = GCodeUtils.getValue(lines[temp_index + 1], "X")
                                                                yPosition = GCodeUtils.getValue(lines[temp_index + 1], "Y")
                                                                del lines[temp_index + 1]
                                                            # Add purge commands
                                                            # todo remove T1/T0 when sigma firmware updated, leave only G71/G72
                                                            if Application.getInstance().getMachineManager().activeMachineId == "Sigma":
                                                                lines[temp_index] += "\n;prevent filament grinding on T" + str(countingForTool) + \
                                                                                    oldLines + \
                                                                                    "\nG1 F" + self._travelSpeed[countingForTool] + \
                                                                                    "\nT" + str(abs(countingForTool - 1)) + \
                                                                                    "\nT" + str(countingForTool) + \
                                                                                    "\nG91" + \
                                                                                    "\nG1 F" + self._travelSpeed[countingForTool] + " Z" + str(self._retractionHopHeightAfterExtruderSwitch[countingForTool]) + \
                                                                                    "\nG90" + \
                                                                                    "\nG1 F" + self._retractionPrimeSpeed[countingForTool] + " E" + str(round(eValue + self._retractionAmount[countingForTool], 5)) + \
                                                                                    "\nG1 F" + self._purgeSpeed[countingForTool] + " E" + str(round(eValue + self._retractionAmount[countingForTool] + purgeLength, 5)) + \
                                                                                    "\nG1 F" + self._retractionRetractSpeed[countingForTool] + " E" + str(round(eValue + purgeLength, 5)) + \
                                                                                    "\nG4 P2000" + \
                                                                                    "\nG92 E" +  str(eValue) + \
                                                                                    "\nG1 F" + self._travelSpeed[countingForTool] + " X" + str(xPosition)+" Y" + str(yPosition) + \
                                                                                    "\nG91" + \
                                                                                    "\nG1 F" + self._travelSpeed[countingForTool] + " Z-" + str(self._retractionHopHeightAfterExtruderSwitch[countingForTool]) + \
                                                                                    "\nG90" + \
                                                                                    "\n;end of the filament grinding prevention protocol"
                                                            else:
                                                                lines[temp_index] += "\n;prevent filament grinding on T" + str(countingForTool) + \
                                                                                    oldLines + \
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
        if self._ZHopAtLayerChange[0] or self._ZHopAtLayerChange[1]:
            self._startGcodeInfo.append("; - Z Hop At Layer Change")
            countingForTool = 0
            for index, layer in enumerate(self._gcode_list):
                lines = layer.split("\n")
                temp_index = 0
                while temp_index < len(lines):
                    line = lines[temp_index]
                    if self._ZHopAtLayerChange[countingForTool] and line.startswith(";LAYER:") and not line.startswith(";LAYER:0"):
                        lines[temp_index] += "\nG91" + \
                                             "\nG1 F" + self._retractionRetractSpeed[countingForTool] + " E-" + str(round(self._retractionAmount[countingForTool], 5)) + \
                                             "\nG1 F" + self._travelSpeed[countingForTool] + " Z" + str(round(self._layerHeight + self._ZHopHeightAtLayerChange[countingForTool], 5)) + " ;z hop at layer change" + \
                                             "\nG1 F" + self._travelSpeed[countingForTool] + " Z-" + str(round(self._layerHeight + self._ZHopHeightAtLayerChange[countingForTool], 5)) + \
                                             "\nG1 F" + self._retractionRetractSpeed[countingForTool] + " E" + str(round(self._retractionAmount[countingForTool], 5)) + \
                                             "\nG90"
                    elif line.startswith("T0"):
                        countingForTool = 0
                    elif line.startswith("T1"):
                        countingForTool = 1
                    temp_index += 1
                layer = "\n".join(lines)
                self._gcode_list[index] = layer
            Logger.log("d", "avoid_grinding_filament applied")

    # def _handleActiveExtruders(self):
    #     # Heat and purge only used extruders. Simultaneously if possible.
    #     if self._activeExtruders:
    #         self._startGcodeInfo.append("; - Heat only essentials")
    #         MachineAllowsClonedExtrusionSteps = self._container.getProperty("print_mode", "enabled")
    #         if self._MEXPrint:
    #             idleExtruder = 'T' + str(abs(int(ExtruderManager.getInstance().getUsedExtruderStacks()[0].getMetaData()['position']) - 1))
    #         startGcodeCorrected = False
    #         for index, layer in enumerate(self._gcode_list):
    #             lines = layer.split("\n")
    #             temp_index = 0
    #             while temp_index < len(lines):
    #                 line = lines[temp_index]
    #                 if not startGcodeCorrected:
    #                     try:
    #                         if line.startswith("M108 P1"):
    #                             del lines[temp_index]
    #                             temp_index -= 1
    #                         line1 = lines[temp_index + 1]
    #                         line2 = lines[temp_index + 2]
    #                         line3 = lines[temp_index + 3]
    #                         line4 = lines[temp_index + 4]
    #                         line5 = lines[temp_index + 5]
    #                         if line1.startswith("G92 E0") and line2.startswith("G1 E") and line3.startswith("G92 E0") and line4.startswith("G4 P2000") and line5.startswith("G1 F2400 E-8"):
    #                             if self._MEXPrint and line.startswith(idleExtruder):
    #                                 # Remove purge lines for unused hotends (MEX Prints)
    #                                 del lines[temp_index]
    #                                 del lines[temp_index]
    #                                 del lines[temp_index]
    #                                 del lines[temp_index]
    #                                 del lines[temp_index]
    #                                 del lines[temp_index]
    #                                 startGcodeCorrected = True
    #                                 break
    #                             elif (self._MirrorOrDuplicationPrint or (self._IDEXPrint and MachineAllowsClonedExtrusionSteps)) and line.startswith("T1"):
    #                                 # Use cloned purge commands if the machine allows it and is using both hotends (IDEX, Mirror or Duplication)
    #                                 del lines[temp_index]
    #                                 del lines[temp_index]
    #                                 del lines[temp_index]
    #                                 del lines[temp_index]
    #                                 del lines[temp_index]
    #                                 del lines[temp_index]
    #                                 lines[temp_index] = lines[temp_index]+"\nM605 S4      ;clone extruders steps"
    #                                 lines[temp_index + 5] = lines[temp_index + 5]+"\nM605 S3      ;back to independent extruder steps"
    #                                 startGcodeCorrected = True
    #                                 break
    #                     except:
    #                         pass
    #                 if self._MEXPrint:
    #                     # Remove heating lines for unused hotends (MEX Prints)
    #                     if idleExtruder == "T1":
    #                         if "T1" in line:
    #                             del lines[temp_index]
    #                             temp_index -= 1
    #                     elif idleExtruder == "T0":
    #                         if index < 2 and (line.startswith("M104 S") or line.startswith("M109 S")) and "T1" not in line:
    #                             del lines[temp_index]
    #                             temp_index -= 1
    #                 temp_index += 1
    #             if startGcodeCorrected:
    #                 layer = "\n".join(lines)
    #                 self._gcode_list[index] = layer
    #                 break
    #         Logger.log("d", "active_extruders applied")
    
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

    # def _handleFixFirstRetract(self):
    #     if self._fixFirstRetract:
    #         self._startGcodeInfo.append("; - Fix First Extrusion")
    #         lookingForTool = None
    #         countingForTool = None
    #         eValueT1 = None
    #         for index, layer in enumerate(self._gcode_list):
    #             lines = layer.split("\n")
    #             if not layer.startswith(";LAYER:"):
    #                 # Get retract value before starting the first layer
    #                 for line in lines:
    #                     if line.startswith("T1"):
    #                         countingForTool = 1
    #                     if countingForTool and GCodeUtils.charsInLine(["G", "F", "E-"], line):
    #                         eValueT1 = GCodeUtils.getValue(line, "E")
    #                         break
    #             else:
    #                 # Fix the thing
    #                 if eValueT1:
    #                     if 'T1\nG92 E0' in layer and layer.startswith(";LAYER:0"):
    #                         # IDEX Starts with T0, then T1. Only T1 needs to be fixed
    #                         # IDEX Starts with T1, then T0. Only T1 needs to be fixed                                
    #                         # MEX  Starts with T1 and only T1 needs to be fixed
    #                         layer = layer.replace('T1\nG92 E0', 'T1\nG92 E'+str(eValueT1)+' ;T1fix', 1)
    #                         break
    #                     elif lookingForTool == 'T1' and 'T1\nG92 E0' in layer:
    #                         # Starts with T0, first T1 found and fixed
    #                         layer = layer.replace('T1\nG92 E0', 'T1\nG92 E'+str(eValueT1)+' ;T1fix', 1)
    #                         break
    #                     elif not lookingForTool:
    #                         # Starts with T0, T1 will need to be fixed
    #                         lookingForTool = 'T1'
    #                 else:
    #                     # There is no eValue to fix and it's already printing
    #                     break
    #         self._gcode_list[index] = layer
    #         Logger.log("d", "fix_retract applied")

    # def _handleSmartPurge(self):
    #     if (self._smartPurge[0] or self._smartPurge[1]) and self._IDEXPrint:
    #         self._startGcodeInfo.append("; - Smart Purge")
    #         for index, layer in enumerate(self._gcode_list):
    #             lines = layer.split("\n")
    #             applyFix = False
    #             if not layer.startswith(";LAYER:0") and layer.startswith(";LAYER:"):
    #                 temp_index = 0
    #                 while temp_index < len(lines):
    #                     if lines[temp_index].startswith("T0") or lines[temp_index].startswith("T1"):
    #                         # toolchange found
    #                         applyFix = True
    #                         toolChangeIndex = temp_index
    #                         if lines[temp_index].startswith("T0"):
    #                             countingForTool = 0
    #                         elif lines[temp_index].startswith("T1"):
    #                             countingForTool = 1
    #                     elif applyFix and self._smartPurge[countingForTool] and GCodeUtils.charsInLine(["G1", "F", "X", "Y", "E"], lines[temp_index]):
    #                         # first extrusion with the new tool found
    #                         extrudeAgainIndex = temp_index
    #                         temp_index = toolChangeIndex
    #                         foundM109 = False
    #                         foundFirstTravel = False
    #                         while temp_index <= extrudeAgainIndex:
    #                             if not foundFirstTravel and GCodeUtils.charsInLine(["G", "F", "X", "Y"], lines[temp_index]):
    #                                 foundFirstTravel = True
    #                                 smartPurgeLineIndex = temp_index - 1
    #                             if lines[temp_index].startswith("M109 S"):
    #                                 foundM109 = True
    #                             elif foundM109 and lines[temp_index].startswith("M104 S"):
    #                                 # remove M104 extra line
    #                                 del lines[temp_index]
    #                                 break
    #                             temp_index += 1
    #                         lines[smartPurgeLineIndex] = lines[smartPurgeLineIndex] + \
    #                                             "\nG1 F" + self._switchExtruderPrimeSpeed[countingForTool] + \
    #                                             " E" + str(self._switchExtruderRetractionAmount[countingForTool]) + \
    #                                             "\nM800 F" + self._purgeSpeed[countingForTool] + \
    #                                             " S" + str(self._smartPurgeSParameter[countingForTool]) + \
    #                                             " E" + str(self._smartPurgeEParameter[countingForTool]) + \
    #                                             " P" + str(self._smartPurgePParameter[countingForTool]) + " ;smartpurge" + \
    #                                             "\nG4 P2000\nG92 E0\nG1 F" + self._retractionRetractSpeed[countingForTool] + \
    #                                             " E-" + str(self._switchExtruderRetractionAmount[countingForTool]) + "\nG92 E0"
    #                         break
    #                     temp_index += 1

    #             layer = "\n".join(lines)
    #             self._gcode_list[index] = layer
    #         Logger.log("d", "smart_purge applied")
                
    # def _handleRetractReduction(self):
    #     if self._retractReduction:
    #         self._startGcodeInfo.append("; - Reduce Retraction")
    #         removeRetracts = False
    #         for index, layer in enumerate(self._gcode_list):
    #             lines = layer.split("\n")
    #             temp_index = 0
    #             if layer.startswith(";LAYER:") and not layer.startswith(";LAYER:0"):
    #                 while temp_index < len(lines):
    #                     line = lines[temp_index]
    #                     if line.startswith(";TYPE:WALL-OUTER") or line.startswith(";TYPE:SKIN") or line.startswith("T"):
    #                         removeRetracts = False
    #                     elif line.startswith(";TYPE:"):
    #                         removeRetracts = True
    #                     if removeRetracts:
    #                         if " E" in line and "G92" not in line:
    #                             eValue = GCodeUtils.getValue(line, "E")
    #                             lineCount = temp_index - 1
    #                             try:
    #                                 if not lines[temp_index + 1].startswith("G92"):
    #                                     while lineCount >= 0:
    #                                         line = lines[lineCount]
    #                                         if " E" in line and "G92" not in line:
    #                                             if eValue < GCodeUtils.getValue(line, "E"):
    #                                                 if removeRetracts:
    #                                                     del lines[temp_index]
    #                                                     temp_index -= 1
    #                                             break
    #                                         lineCount -= 1
    #                             except:
    #                                 break
    #                     temp_index += 1
    #             layer = "\n".join(lines)
    #             self._gcode_list[index] = layer
    #         Logger.log("d", "retract_reduction applied")

    def setMessage(self, message):
        self._message = message

    def _onFinished(self, job):
        if self == job and self._message is not None:
            self._message.hide()
            self._message = None

    def _onProgress(self, job, amount):
        if self == job and self._message:
            self._message.setProgress(amount)