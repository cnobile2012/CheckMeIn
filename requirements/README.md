Definition of the requirement files.

1. requirements/base.txt
   This file has all the packages that are necessary to run the application.
2. requirements/development.txt
   This file has all the packages that are necessary to run the application
   in a development environment. It inherits the base.txt file.
3. requirements/production.txt 
   This file contains the frozen packages which would be regenerated after
   any new or updated packages are added to the base.txt file.
   Generated from the project base directory as such:
   $ pip freeze > requirements/production.txt 
