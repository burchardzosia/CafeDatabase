

def parse_tags_from_str(arg: str): # format: "strategy,action,1 hour,card"
    argList = arg.split(',')
    parsed = []
    for tag in argList:
        parsed.append(tag.strip())
    return parsed

