drop schema book_worm;
create schema book_worm;

use book_worm;

create table books (
	book_id int primary key auto_increment,
	title varchar(200),
    `description` varchar(400),
    `host` varchar(80),
    `link` varchar(400),
    `type` varchar(10),
    size varchar(20),
    `date` varchar(20),
    rate_summary numeric(10, 2)
);
    


    
    
    