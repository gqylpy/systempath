from systempath import SystemPath, Directory, File

root = SystemPath('/')

home: Directory = root['home']['gqylpy']
home.makedirs()

file: File = home['alpha.txt']

file.content = b'GQYLPY \xe6\x94\xb9\xe5\x8f\x98\xe4\xb8\x96\xe7\x95\x8c'
