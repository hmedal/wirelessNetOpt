THIS SCRIPT REQUIRES TWO FILES:

	1)	XML file named "model.xml"
		where the third line/first child MUST be of the form
		<network name="NAME">, where NAME can be:
			1)	Additive
			2)	Protocol
			3)	Capture
			4)	Inf-Range

			If NAME = Inf-Range, the first root MUST be of
			the form <modeltype>value</modeltype>, where value can be:
			
				1)	A
				2)	B

				where:

				model type A reads in a communication and interference ranges
				model type B reads in Cp/Rx Threshhold values

	2)	Text file named "data.txt" with 3 columns:
			1)	node ID # (first should be 0)
			2)	node's X Coordinate
			3)	node's Y Coordinate

		the delimiter should be a space, NOT a comma.
		the delimiter can be changed in the code easily
		in the 4th block of code:
			f = open('data.txt','r')
			for line in f:
			lineArray = line.split(' ')
		simply put a comma instead of a space in the line.split code

Put this script and the two input files in the same directory and then run the script.  

Outputs will appear as connect_G.gml and conflict_G.gml in the same directory.

NOTE:  samples are provided, and you will see various XML files. Please rename each one to "model.xml" so they work with the script, named "Network Generation.py."

NOTE:  As of now, neither GML writings are working. Instead, figures and data are printed to the screen.