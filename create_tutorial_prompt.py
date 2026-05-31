import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--template")
parser.add_argument("-p", "--params")

args = parser.parse_args()

if not args.template:
    print("Need a path to the template file.")
    exit(1)

if not args.params:
    print("Need a path to the params file.")
    exit(1)

if not os.path.exists(args.template):
    print("Invalid file for template.")
    exit(1)

if not os.path.exists(args.params):
    print("Invalid file for params.")
    exit(1)

with open(args.template, "r") as f:
    template = f.read()

with open(args.params, "r") as f:
    params = f.read()


# Parse params
params_lines = params.splitlines()

description = ""
output_path = ""
requirements = ""

for line in params_lines:
    if line.startswith("DESCRIPTION:"):
        description = line.replace("DESCRIPTION:", "")
    elif line.startswith("OUTPUT PATH:"):
        output_path = line.replace("OUTPUT PATH:", "")
    elif line.startswith("REQUIREMENTS:"):
        requirements = line.replace("REQUIREMENTS:", "")
        requirements += "\n"
    else:
        requirements += line + "\n"


final = template.replace("{{description}}", description.strip())
final = final.replace("{{output_path}}", output_path.strip())
final = final.replace("{{requirements}}", requirements.strip())

print(final)
