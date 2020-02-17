import shlex


class Flags:
    commands = {}

    def __init__(self, args: [str]):
        self.args = args

    def Execute(self):
        if len(self.args) <= 1:
            self.printUsage()
            exit(1)

        c = self.args[1]
        funcObj = Flags.commands.get(c, None)
        if not funcObj:
            self.printUsage()
            exit(1)

        funcObj["function"](self.args[2:], self.getKwargs(funcObj["flags"]))

    def getKwargs(self, commandFlags):
        flags = {}
        neededFlags = [x[0] for x in commandFlags]
        for arg in shlex.split(" ".join(self.args)):
            items = arg.split("=")
            if len(items) == 1 and not items[0].startswith("--"):
                continue

            flag = items[0].replace("--", "")
            if len(items) == 1:
                flags[flag] = True
                continue

            value = items[1]
            if flag in neededFlags:
                flags[flag] = value

        retFlags = {}
        for cflag in commandFlags:
            command = cflag[0]
            defaultVal = cflag[2]
            if command in flags:
                if len(cflag) == 4:
                    castFunc = cflag[3]
                    retFlags[command] = castFunc(flags[command])
                else:
                    retFlags[command] = flags[command]
            else:
                if len(cflag) >= 3:
                    retFlags[command] = defaultVal

        return retFlags


    def printUsage(self):
        for fObj in Flags.commands.values():
            print(f"{fObj['name']:<16} : {fObj['usage']}")
            for arg in fObj["flags"]:
                default = ""
                if len(arg) >= 3:
                    default = f"(default: {arg[2]})"
                print(f"{'--' + arg[0]:>16} = {arg[1]} {default}")

    @staticmethod
    def asCommand(functionName: object, **kwargs):
        """

        :rtype: function
        """
        def acDecorator(f):
            Flags.commands[functionName] = {
                "name": functionName,
                "function": f,
                "usage": kwargs.get("usage", ""),
                "flags": kwargs.get("flags", [])
            }
            return f

        return acDecorator