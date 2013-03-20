###Here is a parser for IOmeter result.
--- 
####Benchmark1:
Three key parameters decide the output which are sample space, IO size and test amount.
- Sample Space	: the 'Maximum Disk Size' attribute stored in list *spaces*;
- IO Size		: the access specification attribute stored in list *size*;
- Test amount	: the amount stored in variable *interval* which test case runs, the output result is the average of these thests.

####Benchmark2:
Two key parameters including:
- specs: the specifications of all cases
- managers: the managers of each case

The output contains three matrix including IOPS matrix, Bandwidth matrix and Lantency matrix.
