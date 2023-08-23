#!/usr/bin/expect -f

spawn mariadb -u root -p
expect "Enter password:"
send "csi\n"
expect "MariaDB"
send "USE OUSS;\n"
interact
