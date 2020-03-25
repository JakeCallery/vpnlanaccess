import os
import platform
import re
from subprocess import check_output

DEBUG_MODE = os.getenv("VPN_LAN_ACCESS_DEBUG")

if (DEBUG_MODE):
    print("WARNING: Running in DEBUG_MODE")


def main():
    interface_list = []

    print("Checking for supported Operating System...")
    platform_os = platform.system()
    platform_version = platform.version()
    print("Operating system is: " + platform_os + " " + str(platform_version))

    if platform_os != "Windows":
        print("ERROR: This script is meant for Windows 7 or Windows 10 ONLY.")
        print("This machine was detected as running: " + platform_os + " " + str(platform_version))
        exit(1)

    if not (platform_version.startswith("10.0") or platform_version.startswith("6.1")):
        print("ERROR: This script is meant for Windows 7 or Windows 10 ONLY.")
        exit(1)

    print("Checking for administrator rights...")
    try:
        check_output("net session >nul 2>&1", shell=True)
    except Exception as e:
        print("\nERROR: You do not appear to have administrator rights in this prompt.")
        print(
            "Please click on the Windows Start Button -> Type: cmd -> Right Click on Command Prompt -> Select \"Run "
            "As Administrator\"")
        print("Then please re-run this utility from that prompt.\n")
        if DEBUG_MODE:
            pass
        else:
            exit(1)

    # Get nics from ipconfig
    output = check_output("ipconfig /all", shell=True)
    ip_output = output.split(os.linesep)

    # Parse ipconfig and create interface objects
    i = 0
    interface = None
    parsing_interface = False
    while i < len(ip_output):
        i_line = ip_output[i].strip()

        if i_line.startswith("Description"):
            # Found new Interface
            parsing_interface = True
            interface = {"desc": str(i_line).strip().split(": ")[1]}

        if parsing_interface:
            if i_line.startswith("Physical Address"):
                interface["mac"] = str(i_line).strip().split(": ")[1]

            if i_line.startswith("IPv4 Address"):
                ip = str(i_line).strip().split(": ")[1]
                if ip.endswith("(Preferred)"):
                    ip = ip[:-11]
                interface["ip"] = ip

            if i_line.startswith("Subnet Mask"):
                interface["mask"] = str(i_line).strip().split(": ")[1]

            if i_line.startswith("Default Gateway"):
                interface["gateway"] = str(i_line).strip().split(": ")[1]

            if i_line == "":
                interface_list.append(interface)
                parsing_interface = False
        i = i+1

    # Last interface check
    if len(interface_list) < 1:
        print("ERROR: Unable to find any active network interfaces.")
        exit(1)

    # Parse route print to get interface index based on mac
    route_output = check_output("route print", shell=True)
    route_lines = route_output.split(os.linesep)
    for r in range(len(route_lines)):
        route_line = route_lines[r].strip()
        if route_line.startswith("Interface List"):
            ilist_index = r + 1
            while not route_lines[ilist_index].strip().startswith("=="):
                ilist_line = route_lines[ilist_index].strip()
                # match up mac address in interface list and store interface index
                ilist_line = re.sub(r'\.+', '|', ilist_line)
                tokens = ilist_line.split('|')
                if len(tokens) == 3:
                    idx = tokens[0]
                    ilist_mac = tokens[1].strip().replace(" ", "-")
                    for interface in interface_list:
                        if ilist_mac.upper() == interface["mac"]:
                            interface["idx"] = idx
                            break
                ilist_index = ilist_index + 1

    #Remove non-active interfaces
    for x in range(len(interface_list)-1, -1, -1):
        if "ip" not in interface_list[x]:
            interface_list.pop(x)

    print interface_list

    # Print list of interfaces for user to choose from
    if len(interface_list) < 2:
        print(
            "\nWARNING: Only found one active network interface, please be sure you are already connected to the VPN "
            "before continuing!\b")
    print("\n\n")

    for i in range(len(interface_list)):
        print(str(i + 1) + ": " + interface_list[i]["desc"])
        print(str(interface_list[i]["ip"]) + "\n")

    # Ask user to select local ip
    ip_selection_input = raw_input(
        "Please enter the number of your LOCAL (non-vpn) ip address from the list 1-" + str(len(interface_list)) + ": ")

    try:
        int(ip_selection_input)
        valid_input_type = True
    except ValueError:
        valid_input_type = False

    if valid_input_type:
        if 1 <= int(ip_selection_input) <= len(interface_list):
            # save off nic info
            local_interface = interface_list[int(ip_selection_input) - 1]
            print local_interface

            # only supporting 255.255.255.0 mask for now
            if local_interface["mask"] == "255.255.255.0":
                route_commands = []
                octet_list = local_interface["ip"].split(".")
                first_three = octet_list[0] + "." + octet_list[1] + "." + octet_list[2]

                route_commands.append(
                    "route delete " + octet_list[0] + "." + octet_list[1] + "." + octet_list[2] + "." + "0")
                route_commands.append(
                    "route delete " + octet_list[0] + "." + octet_list[1] + "." + octet_list[2] + "." + "255")
                route_commands.append(
                    "route delete " + octet_list[0] + "." + octet_list[1] + "." + octet_list[2] + "." + "128")
                route_commands.append("route delete " + local_interface["ip"])
                route_commands.append("route add " + first_three + ".0" +
                                      " MASK " + local_interface["mask"] +
                                      " " + local_interface["gateway"] +
                                      " " + "IF " + local_interface["idx"] +
                                      " " + "METRIC 1")
                route_commands.append("route change " + first_three + ".0" +
                                      " MASK " + local_interface["mask"] +
                                      " " + local_interface["gateway"] +
                                      " " + "IF " + local_interface["idx"] +
                                      " " + "METRIC 1")

                print("Proposed Route Changes:")
                for command in route_commands:
                    print(command)

                run_commands_input = raw_input("Commit the changes(Y/N)?")

                if run_commands_input.lower() == "y":
                    for command in route_commands:
                        try:
                            print("Running: " + command)
                            if not DEBUG_MODE:
                                response = check_output(command, shell=True)
                                print(response)
                            else:
                                print("Skipped running command because debug mode is set.")

                        except Exception as e:
                            print("ERROR: route command failed: " + e.message)
                else:
                    print("Route changes NOT committed, exiting")
                    exit(0)
            else:
                print(
                    "ERROR: This version of the app is currently only able to handle local ips with a netmask of "
                    "255.255.255.0")
                print(
                    "To get an updated version of the app, make sure you are on the vpn, and run the following from "
                    "the command line:")
                print("route print > c:\\temp\\routes.txt")
                print("Then email the c:\\temp\\routes.txt to jake.callery@ansys.com")
        else:
            print("ERROR: That does not seem like one of the options, valid inputs are integers between 1 and " + str(
                len(interface_list)))
            exit(1)
    else:
        print("ERROR: That does not seem like one of the options, valid inputs are integers between 1 and " + str(
            len(interface_list)))
        exit(1)


if __name__ == "__main__":
    main()
