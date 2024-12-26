-- table's DDL

CREATE TABLE jobs (
    id INTEGER,
    job VARCHAR(255) NOT NULL
);

CREATE TABLE departments (
    id INTEGER,
    department VARCHAR(255) NOT NULL
);


CREATE TABLE hired_employees (
    id INTEGER,
    name VARCHAR(255) ,
    datetime VARCHAR(255) ,
    department_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL
);

-- testing tables
select * from jobs;
select * from departments;
select * from hired_employees;

-- Requirement 1
with base_previa as (
select b.department,
		c.job,
count(case when EXTRACT(MONTH FROM TO_DATE(a.datetime, 'YYYY-MM-DD"T"HH24:MI:SS"Z"')) between 1 and 3 then 1 end  ) as Q1,
count(case when EXTRACT(MONTH FROM TO_DATE(a.datetime, 'YYYY-MM-DD"T"HH24:MI:SS"Z"')) between 4 and 6 then 1 end  ) as Q2,
count(case when EXTRACT(MONTH FROM TO_DATE(a.datetime, 'YYYY-MM-DD"T"HH24:MI:SS"Z"')) between 7 and 9 then 1 end  ) as Q3,
count(case when EXTRACT(MONTH FROM TO_DATE(a.datetime, 'YYYY-MM-DD"T"HH24:MI:SS"Z"')) between 10 and 12 then 1 end  ) as Q4
from hired_employees as a 
left join departments as b on a.department_id =b.id
left join jobs as c on a.job_id =c.id
where EXTRACT(YEAR FROM TO_DATE(a.datetime, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'))=2021
group by 1,2
)
select * from base_previa
where not (department is null or JOB is null)
order by 1,2;

-- Requirement 2
with PREV_A as (
select 
b.department,count(1) as ctd
from hired_employees a 
left join departments b on a.department_id =b.id
where EXTRACT(YEAR FROM TO_DATE(a.datetime, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'))=2021
and DEPARTMENT is not null 
group by b.department
), MEAN_TABLE as (
select b.id,
b.department, c.mean, count(1) as HIRED
from hired_employees a 
left join departments b on a.department_id =b.id
left join (select AVG(CTD) as mean from PREV_A) c on 1=1 
where EXTRACT(YEAR FROM TO_DATE(a.datetime, 'YYYY-MM-DD"T"HH24:MI:SS"Z"'))=2021
and DEPARTMENT is not null
group by 1,2,3
)
select id,department,hired 
from mean_table
where hired>mean
order by 3 desc;