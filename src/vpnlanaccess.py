import os
import platform
from subprocess import check_output

DEBUG_MODE = os.getenv("VPN_LAN_ACCESS_DEBUG")

if(DEBUG_MODE):
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
		net_sess_output = check_output("net session >nul 2>&1", shell=True)
	except Exception as e:
		print("\nERROR: You do not appear to have administrator rights in this prompt.")
		print("Please click on the Windows Start Button -> Type: cmd -> Right Click on Command Prompt -> Select \"Run As Administrator\"")
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
						"ip": str(ip).strip(),
						"mask": str(str(ip_output[k+1]).split(" :")[1]).strip(),
						"gateway": str(str(ip_output[k+2]).split(" :")[1]).strip()
					}

					interface_list.append(interface)
					break
				k = k+1
				i = k
		i = i + 1

# Print list of interfaces for user
	if len(interface_list) < 1:
		print("ERROR: Unable to find any active network interfaces.")
		exit(1)

	if len(interface_list) < 2:
		print("\nWARNING: Only found one active network interface, please be sure you are already connected to the VPN before continuing!\b")

	for i in range(len(interface_list)):

		print(str(i+1) + ": " + interface_list[i]["desc"])
		print(str(interface_list[i]["ip"]) + "\n")

# Ask user to select local ip
	ip_selection = raw_input("Please enter the number of your LOCAL (non-vpn) ip address from the list 1-" + str(len(interface_list)) + ": ")



if __name__ == "__main__":
	main()
