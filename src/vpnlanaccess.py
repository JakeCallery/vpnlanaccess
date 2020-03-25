import os
import platform
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

    # Get active nics
    output = check_output("ipconfig /all", shell=True)
    ip_output = output.split(os.linesep)

    # Parse ipconfig and create interface objects
    i = 0
    while i < len(ip_output):
        i_line = ip_output[i].strip()

        if i_line.startswith("Description"):
            # Find IPV4 line
            k = i
            while k < len(ip_output):
                k_line = str(ip_output[k]).strip()
                if k_line.startswith("IPv4 Address") or k_line.startswith("IP Address"):
                    ip = k_line.split(" :")[1]
                    if ip.endswith("(Preferred)"):
                        ip = ip[:-11]
                    interface = {
                        "desc": str(i_line).strip().split(": ")[1],
                        "mac": str(ip_output[i+1].split(": ")[1]),
                        "ip": str(ip).strip(),
                        "mask": str(str(ip_output[k + 1]).split(" :")[1]).strip(),
                        "gateway": str(str(ip_output[k + 4]).split(" :")[1]).strip()
                    }

                    print interface
                    interface_list.append(interface)
                    break
                k = k + 1
            i = k
        i = i + 1

    # Parse route print to get interface index based on mac

    # Print list of interfaces for user
    if len(interface_list) < 1:
        print("ERROR: Unable to find any active network interfaces.")
        exit(1)

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
                                      " " + "METRIC 1")
                route_commands.append("route change " + first_three + ".0" +
                                      " MASK " + local_interface["mask"] +
                                      " " + local_interface["gateway"] +
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
