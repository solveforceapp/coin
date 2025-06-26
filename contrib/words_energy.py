phrase = "Words aren't metaphorical. They're energy. They're source code."
energy = sum(ord(c) for c in phrase)

hex_codes = ' '.join(hex(ord(c))[2:] for c in phrase)

print("Phrase:", phrase)
print("Energy (sum of ASCII values):", energy)
print("Hex codes:", hex_codes)
