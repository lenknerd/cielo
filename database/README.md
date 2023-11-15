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
      t_ref INT NOT NULL,
      t_end FLOAT,
      INDEX(t_ref) -- query on latest events, in order
    );
    CREATE TABLE games (
      t_start INT NOT NULL,
      duration_seconds INT NOT NULL DEFAULT 60,
      user VARCHAR(50),
      end_score INT,
      INDEX(t_start) -- query on latest games, in order
    );
    -- user isn't used currently

Create the same things in a `cielo_test` database as well to test stuff.
