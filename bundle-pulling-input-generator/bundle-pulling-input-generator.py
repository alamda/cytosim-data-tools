#!/usr/bin/python

"""Order of thangs

Much simpler version for now:
Inputs: number of pulls, distance per pull, and time between pulls
Output: file with the pulling commands to append at the end of a cytosim input file

Read config.tpl file
- property of system
- properties of filaments
- number of anchor filaments
- number of puller filaments in groups A and B
- number of free filaments
- properties of anchor singles
- properties of puller singles
- properties of active couples
- number of motors (active couples)
- nucleation steps
- pulling parameters (distance (x) + speed + strength)
	- strength is controlled by stiffness (k) of puller singles

F = kx


Questions to consider (after input generation things are more or less functional):
- is there an optimal stiffness to the puller singles?
- how to determine the best speed for pulling?
	- pulling speed probably a function of active couple stiffness
"""

"""Example pulling code
% Begin pulling
for CNT=0 :10 {
        new pullerB
        {
                attach = actin_pullCNT, 0.125
                position = (0.1 0)
        }
}

delete all pullerA

run system
{
        nb_steps = 100
        nb_frames = 1
}

% pull #2
for CNT=0 :10 {
        new pullerA
        {
                attach = actin_pullCNT, 0.125
                position = (0.2 0)
        }
}

delete all pullerB

run system
{
        nb_steps = 100
        nb_frames = 1
}
"""
import sys
import argparse # for parsing command line arguments to script

def get_args():
	"""Parse the command line input flags and arguments
	inptus: number of pulls, distance per pull, and time between pulls
	"""

	parser = argparse.ArgumentParser(description='')

	parser.add_argument('--npulls', '-n', type=int, help='number of pulls')
	parser.add_argument('--dist', '-d', type=float, help='distance per pull')
	parser.add_argument('--steps', '-s', type=int, help='steps between pulls')
	parser.add_argument('--ofile', '-o', type=str, help='name of output file')

	args = parser.parse_args()

	return args

def write_protocol(args):
	output_file_name = args.ofile

	if not output_file_name:
		output_file_name = "pull.cym"

	n_pulls = args.npulls
	dist_per_pull = args.dist
	steps_bw_pulls = args.steps

	frames_bw_pulls = int(steps_bw_pulls//100)

	pullerA_exists = True
	puller_to_create = "pullerB"
	puller_to_delete = "pullerA"

	puller_position = 0.0

	with open(output_file_name, 'w') as out_file:
		for pull_idx in range(n_pulls):
			if pullerA_exists:
				puller_to_create = "pullerB"
				puller_to_delete = "pullerA"
				pullerA_exists = False
			else:
				puller_to_create = "pullerA"
				puller_to_delete = "pullerB"
				pullerA_exists = True

			puller_position+=dist_per_pull

			output_str = ""
			output_str+="for CNT=0 :10\n{\n"
			output_str+="\tnew %s\n"%puller_to_create
			output_str+="\t{\n"
			output_str+="\t\tattach = actin_pullCNT, 0.125\n"
			output_str+="\t\tposition = (%f 0)\n"%puller_position
			output_str+="\t}\n"
			output_str+="}\n"
			output_str+="delete all %s\n"%puller_to_delete
			output_str+="run system\n{\n\tnb_steps = %i\n\tnb_frames = %i\n}\n\n"%(steps_bw_pulls,frames_bw_pulls)

			# print(output_str)
			out_file.write(output_str)

def main(argv):
	# Get file name(s) from command line arguments
	args = get_args()
	write_protocol(args)

if __name__ == "__main__":
	main(sys.argv[1:])
