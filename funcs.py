
def GetOSicon(os):
    new_icon = 'collage'  # Default if OS not known
    if(os == 'Windows'):
        new_icon = 'microsoft'
    elif(os == 'Linux'):
        new_icon = 'penguin'
    elif(os == 'macOS'):
        new_icon = 'apple'
    return new_icon
