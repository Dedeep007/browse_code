raw_ascii = """
██████████████████████████████
██████████████████████████████
███████████▒▒▒▒▓█▓▒▒▒▒████████
██████████▒▒▒▒▒▓█▓▒▒▒▒▒███████
█████████▓▒▒▒███████▒▒▒▓██████
█████████▓▒▒▒███████▒▒▒▓██████
█████████▓▒▒▒███████▓▒▒▓██████
█████████▒▒▒▓███████▓▒▒▒██████
███████▒▒▒▒▓█████████▓▒▒▒▒████
███████▒▒▒▒▓█████████▓▒▒▒▒████
█████████▒▒▒▓███████▓▒▒▒██████
█████████▓▒▒▓███████▓▒▒▓██████
█████████▓▒▒▒███████▒▒▒▓██████
█████████▓▒▒▒███████▒▒▒▓██████
█████████▓▒▒▒███████▒▒▒▓██████
██████████▒▒▒▒▒▓█▓▒▒▒▒▒███████
███████████▓▒▒▒▓█▓▒▒▒▓████████
██████████████████████████████
"""

# Let's replace the left bracket with [bold green]...[/bold green]
# and the right bracket with [bold red]...[/bold red]

formatted_lines = []
for line in raw_ascii.strip().split("\n"):
    # Since the image is 30 chars wide and perfectly symmetrical,
    # let's split it down the middle (15 chars)
    left_half = line[:15]
    right_half = line[15:]
    
    # We color the left half green and the right half red
    # Wait, the user wants the bracket colored. 
    # If we color the whole half, the background `█` will also be colored.
    # To color ONLY the bracket, we can replace `▒` and `▓` in the left half with green,
    # and in the right half with red.
    
    left_colored = ""
    for char in left_half:
        if char in "▒▓":
            left_colored += f"[bold green]{char}[/bold green]"
        else:
            left_colored += char
            
    right_colored = ""
    for char in right_half:
        if char in "▒▓":
            right_colored += f"[bold red]{char}[/bold red]"
        else:
            right_colored += char
            
    formatted_lines.append(f'    "{left_colored}{right_colored}",')

with open("colored_ascii.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(formatted_lines))
