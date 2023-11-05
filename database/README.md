# Database Installation and Setup

MariaDB is a fork of MySQL which has a compatible distribution for Raspberry Pi. Following [this install for MariaDB on Raspberry Pi](https://raspberrytips.com/install-mariadb-raspberry-pi/):

    sudo apt install mariadb-server
    sudo mysql_secure_installation

Then set up a simple (not so secure but localhost-available-only) database and user;

    mysql -uroot

    CREATE DATABASE cielo;
    CREATE USER 'cielo'@'localhost' IDENTIFIED BY 'cielo';
    GRANT ALL PRIVILEGES ON cielo.* TO 'cielo'@'localhost';
    FLUSH PRIVILEGES;

Log in and create the tables in the public schema;

    mysql -ucielo -p

    USE cielo;
    CREATE TABLE events (
      kind VARCHAR(20) NOT NULL,
      t_ref TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      t_end TIMESTAMP
    );
    CREATE TABLE games (
      t_start TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      duration_seconds INT,
      user VARCHAR(50)
    );
    -- user isn't used currently
