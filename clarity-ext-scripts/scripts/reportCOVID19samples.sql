-- This query returns all currently known samples with their UDFs of project 'Covid19'
/*
select --count(*)
p.luid as "LimsId", s.name as "Name", 
	pf1.text7 as "Biobank barcode", 
	pf2.text5 as "CT latest date",
	pf3.text6 as "CT source",
	pf4.text7 as "Control",
	pf5.text4 as "Control type",
	round(pf6.numeric8::numeric, 10)::float8 as "FAM-CT latest",
	pf7.text8 as "KNM data added at",
	pf8.text9 as "KNM org URI",
	pf9.text0 as "KNM result uploaded",
	pf10.text1 as "KNM result uploaded date",
	pf11.text3 as "KNM service request id", 
	pf12.text4 as "KNM uploaded source",
	pf13.text5 as "Sample Buffer",
	pf14.text3 as "SmiNet artifact source",
	pf15.text4 as "SmiNet last error",
	pf16.text5 as "SmiNet status",
	pf17.text6 as "SmiNet uploaded date",
	pf18.text0 as "Source",
	pf19.text1 as "Status",
	pf20.text2 as "Status artifact source",
	pf21.text9 as "Step ID created in", 
	round(pf22.numeric10::numeric, 10)::float8 as "VIC-CT latest",
	pf23.text6 as "rtPCR Passed latest",
	pf24.text5 as "rtPCR covid-19 result latest"
from sample s inner join process p using(processid)
	left join processudfstorage pf1 on s.processid = pf1.processid and pf1.rowindex = 3
	left join processudfstorage pf2 on s.processid = pf2.processid and pf2.rowindex = 2
	left join processudfstorage pf3 on s.processid = pf3.processid and pf3.rowindex = 2
	left join processudfstorage pf4 on s.processid = pf4.processid and pf4.rowindex = 1
	left join processudfstorage pf5 on s.processid = pf5.processid and pf5.rowindex = 2
	left join processudfstorage pf6 on s.processid = pf6.processid and pf6.rowindex = 0
	left join processudfstorage pf7 on s.processid = pf7.processid and pf7.rowindex = 2
	left join processudfstorage pf8 on s.processid = pf8.processid and pf8.rowindex = 2
	left join processudfstorage pf9 on s.processid = pf9.processid and pf9.rowindex = 3
	left join processudfstorage pf10 on s.processid = pf10.processid and pf10.rowindex = 3
	left join processudfstorage pf11 on s.processid = pf11.processid and pf11.rowindex = 3
	left join processudfstorage pf12 on s.processid = pf12.processid and pf12.rowindex = 3
	left join processudfstorage pf13 on s.processid = pf13.processid and pf13.rowindex = 0
	left join processudfstorage pf14 on s.processid = pf14.processid and pf14.rowindex = 4
	left join processudfstorage pf15 on s.processid = pf15.processid and pf15.rowindex = 4
	left join processudfstorage pf16 on s.processid = pf16.processid and pf16.rowindex = 4
	left join processudfstorage pf17 on s.processid = pf17.processid and pf17.rowindex = 4
	left join processudfstorage pf18 on s.processid = pf18.processid and pf18.rowindex = 4
	left join processudfstorage pf19 on s.processid = pf19.processid and pf19.rowindex = 4
	left join processudfstorage pf20 on s.processid = pf20.processid and pf20.rowindex = 4
	left join processudfstorage pf21 on s.processid = pf21.processid and pf21.rowindex = 3
	left join processudfstorage pf22 on s.processid = pf22.processid and pf22.rowindex = 0
	left join processudfstorage pf23 on s.processid = pf23.processid and pf23.rowindex = 3
	left join processudfstorage pf24 on s.processid = pf24.processid and pf24.rowindex = 3
where s.projectid = 951 -- Covid19 project on prod01
--where s.projectid = 1001 -- Test-Covid19 project on prod01
--where s.projectid = 801 -- Covid19 project on stage01
--where s.projectid = 751 -- Test-Covid19 on stage01
--	and s.datereceived < to_date('2020-07-15', 'YYYY-MM-DD')
order by 1;
*/
select --count(*)
p.luid as "LimsId", s.name as "Name", 
	pf1.text3 as "Biobank barcode", 
	pf2.text5 as "CT latest date",
	pf3.text6 as "CT source",
	round(pf4.numeric3::numeric, 10)::float8 as "Control", --pf4.text7 as "Control",	-- HERE is IT!
	pf5.text4 as "Control type",
	round(pf6.numeric6::numeric, 10)::float8 as "FAM-CT latest",
	pf7.text7 as "KNM data added at",
	pf8.text8 as "KNM org URI",
	pf9.text9 as "KNM result uploaded",
	pf10.text0 as "KNM result uploaded date",
	pf11.text2 as "KNM service request id", 
	pf12.text3 as "KNM uploaded source",
	pf13.text7 as "Sample Buffer",
	pf14.text8 as "SmiNet artifact source",
	pf15.text9 as "SmiNet last error",
	pf16.text0 as "SmiNet status",
	pf17.text1 as "SmiNet uploaded date",
	pf18.text2 as "Source",
	pf19.text3 as "Status",
	pf20.text4 as "Status artifact source",
	pf21.text5 as "Step ID created in", 
	round(pf22.numeric8::numeric, 10)::float8 as "VIC-CT latest",
	pf23.text6 as "rtPCR Passed latest",
	pf24.text5 as "rtPCR covid-19 result latest"
--	pf. as "",
from sample s inner join process p using(processid)
	left join processudfstorage pf1 on s.processid = pf1.processid and pf1.rowindex = 0
	left join processudfstorage pf2 on s.processid = pf2.processid and pf2.rowindex = 0
	left join processudfstorage pf3 on s.processid = pf3.processid and pf3.rowindex = 0
	left join processudfstorage pf4 on s.processid = pf4.processid and pf4.rowindex = 0
	left join processudfstorage pf5 on s.processid = pf5.processid and pf5.rowindex = 0
	left join processudfstorage pf6 on s.processid = pf6.processid and pf6.rowindex = 0
	left join processudfstorage pf7 on s.processid = pf7.processid and pf7.rowindex = 0
	left join processudfstorage pf8 on s.processid = pf8.processid and pf8.rowindex = 0
	left join processudfstorage pf9 on s.processid = pf9.processid and pf9.rowindex = 0
	left join processudfstorage pf10 on s.processid = pf10.processid and pf10.rowindex = 1
	left join processudfstorage pf11 on s.processid = pf11.processid and pf11.rowindex = 1
	left join processudfstorage pf12 on s.processid = pf12.processid and pf12.rowindex = 1
	left join processudfstorage pf13 on s.processid = pf13.processid and pf13.rowindex = 1
	left join processudfstorage pf14 on s.processid = pf14.processid and pf14.rowindex = 1
	left join processudfstorage pf15 on s.processid = pf15.processid and pf15.rowindex = 1
	left join processudfstorage pf16 on s.processid = pf16.processid and pf16.rowindex = 2
	left join processudfstorage pf17 on s.processid = pf17.processid and pf17.rowindex = 2
	left join processudfstorage pf18 on s.processid = pf18.processid and pf18.rowindex = 2
	left join processudfstorage pf19 on s.processid = pf19.processid and pf19.rowindex = 2
	left join processudfstorage pf20 on s.processid = pf20.processid and pf20.rowindex = 2
	left join processudfstorage pf21 on s.processid = pf21.processid and pf21.rowindex = 2
	left join processudfstorage pf22 on s.processid = pf22.processid and pf22.rowindex = 0
	left join processudfstorage pf23 on s.processid = pf23.processid and pf23.rowindex = 1
	left join processudfstorage pf24 on s.processid = pf24.processid and pf24.rowindex = 1
where projectid = 3		-- prod02
--where s.projectid = 2 -- COVID_Test project on prod02
--where s.projectid = 51 -- COVID_Test project on stage02
--where s.projectid = 101 -- Covid19 project on stage02order by 1 desc;
order by 1;
