from ..Script import Script
# from cura.Settings.ExtruderManager import ExtruderManager

class PauseAtHeightBCN3D(Script):
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Pause at height - BCN3D",
            "key": "PauseAtHeightBCN3D",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "pause_height":
                {
                    "label": "Pause Height",
                    "description": "At what height should the pause occur. Warning: SD prints only.",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 5.0
                }
            }
        }"""

    def execute(self, data: list):

        """data is a list. Each index contains a layer"""

        current_z = 0.
        layers_started = False
        pause_height = self.getSettingValueByKey("pause_height")

        # use offset to calculate the current height: <current_height> = <current_z> - <layer_0_z>
        layer_0_z = 0.
        got_first_g_cmd_on_layer_0 = False
        for layer in data:
            lines = layer.split("\n")
            for line in lines:
                if ";LAYER:0" in line:
                    layers_started = True
                    continue

                if not layers_started:
                    continue

                if (self.getValue(line, 'G') == 1 or self.getValue(line, 'G') == 0) and 'X' in line and 'Y' in line and 'Z' in line:
                    current_z = self.getValue(line, 'Z')
                    if not got_first_g_cmd_on_layer_0:
                        layer_0_z = current_z
                        got_first_g_cmd_on_layer_0 = True

                    if current_z is not None:
                        current_height = current_z - layer_0_z
                        if current_height >= pause_height:
                            index = data.index(layer)

                            prepend_gcode = ";TYPE:CUSTOM\n"
                            prepend_gcode += ";added code by post processing\n"
                            prepend_gcode += ";script: PauseAtHeight - BCN3D.py\n"
                            prepend_gcode += ";current z: %f \n" % current_z
                            prepend_gcode += ";current height: %f \n" % current_height
                            prepend_gcode += "G69 ;park active hotend\n"
                            prepend_gcode += "M25 ;stop SD reading\n"
                            prepend_gcode += "G4 P1\n"
                            prepend_gcode += "G4 P2\n"
                            prepend_gcode += "G4 P3\n"

                            layer = prepend_gcode + layer

                            # Override the data of this layer with the
                            # modified data
                            data[index] = layer
                            return data
                        break
        return data
