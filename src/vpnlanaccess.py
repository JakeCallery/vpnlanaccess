import os
import platform
from subprocess import check_output


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
		print("ERROR: You do not appear to have administrator rights in this prompt.")
		print("Please click on the Windows Start Button -> Type: cmd -> Right Click on Command Prompt -> Select \"Run As Administrator\"")
		print("Then please re-run this utility from that prompt.")
		exit(1)

	# Get active nics
	output = check_output("ipconfig", shell=True)
	ip_output = output.split(os.linesep)

	i = 0
	while i < len(ip_output):
		line = ip_output[i].strip()

		if line.startswith("IPv4 Address") or line.startswith("IP Address"):
			ip = line.split(" :")[1]
			interface = {
				"ip": str(ip),
				"mask": str(str(ip_output[i+1]).split(" :")[1]),
				"gateway": str(str(ip_output[i+2]).split(" :")[1])
			}

			interface_list.append(interface)
			i = i + 2
		i = i + 1

	# ask user for local interface
	if len(interface_list) < 1:
		print("ERROR: Unable to find any active network interfaces.")
		exit(1)

	for i in range(len(interface_list)):
		print(str(i+1) + ": " + interface_list[i]["ip"])

	ip_selection = raw_input("Please enter the number of your local ip address from the list 1 - " + str(len(interface_list)) + ": ")
	print ip_selection



if __name__ == "__main__":
	main()
