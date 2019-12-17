-- name: get-all
-- Get all user records
select * from users;

-- name: get-all-sorted
-- Get all user records sorted by username
select * from users order by username asc;

-- name: get-one?
-- Get one user based on its id
select username, firstname, lastname from users where userid = %s;
