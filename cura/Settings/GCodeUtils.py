import re

def getPurgeSpeed(lines, tempIndex):
    lineCount = tempIndex - 1
    purgeSpeed = 25
    while lineCount + 1 < len(lines):
        line0 = lines[lineCount]
        line1 = lines[lineCount + 1]
        if charsInLine("GFXYE", line0) and charsInLine("GXYE", line1):
            fValue = getValue(line0, "F")
            x0Value, y0Value, e0Value = getValue(line0, "X"), getValue(line0, "Y"), getValue(
                line0, "E")
            x1Value, y1Value, e1Value = getValue(line1, "X"), getValue(line1, "Y"), getValue(
                line1, "E")
            movedDistance = ((x1Value - x0Value) ** 2 + (y1Value - y0Value) ** 2) ** 0.5
            extrudedDistance = e1Value - e0Value
            timeExtruding = 1 / (fValue / 60.) * movedDistance
            purgeSpeed = extrudedDistance / timeExtruding * 60 * 2  # multiplied by 2 to speed up the process
            break
        lineCount += 1
    return round(purgeSpeed, 5)


def charsInLine(characters, line):
    for c in characters:
        if c not in line:
            return False
    return True

##  Convenience function that finds the value in a line of g-code.
#   When requesting key = x from line "G1 X100" the value 100 is returned.
def getValue(line, key, default=None):
    if not key in line or (';' in line and line.find(key) > line.find(';')):
        return default
    sub_part = line[line.find(key) + 1:]
    m = re.search('^-?[0-9]+\.?[0-9]*', sub_part)
    if m is None:
        return default
    try:
        return float(m.group(0))
    except:
        return default