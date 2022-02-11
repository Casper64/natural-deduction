
statements: list[str] = []

def read_from_file(path: str) -> None:
    file = open(path)
    lines = file.readlines()
    for line in lines:
        line = line.strip()
        if len(line) > 0:
            if line[0] != "#":
                statements.append(line)

def read_from_input() -> None:
    print("Your statement: ", end="")
    statement = input()
    statements.append(statement)