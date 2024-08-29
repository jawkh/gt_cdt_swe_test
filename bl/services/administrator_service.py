# Copyright (c) 2024 by Jonathan AW
# administrator_service.py

"""
# Summary:
The AdministratorService class provides a comprehensive implementation of the business logic related to administrators. 

# Design Patterns:
1. Comprehensive Functionality:
- The class covers all necessary CRUD operations and additional functionalities like password management and account locking/unlocking.

2. Clear Separation of Concerns:
- Each method is responsible for a specific piece of logic related to administrators, adhering to the Single Responsibility Principle (SRP).

3. Use of Security Best Practices:
- The use of salt and hashing for password management is a good security practice to protect stored passwords.
- The implementation of account locking after too many failed login attempts enhances security against brute-force attacks.

4. Use of Custom Exceptions:
- The use of AdministratorNotFoundException for handling cases where administrators are not found is good for clarity and debugging.

5. Environment Configuration:
- Loading environment variables for configurations like MAX_PASSWORD_RETRIES and PASSWORD_RETRIES_TIME_WINDOW_MINUTES is a good practice to avoid hardcoding values.

"""

import hashlib
import os
from typing import Optional, List
from dal.crud_operations import CRUDOperations
from dal.models import Administrator
from exceptions import InvalidAdministratorDataException, AdministratorNotFoundException 
from environs import Env
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
load_dotenv()
from utils.data_validation import validate_administrator_data
class AdministratorService:
    # Load environment variables

    """
    Service class to handle all business logic related to administrators.
    """
    MAX_PASSWORD_RETRIES = int(Env().str("MAX_PASSWORD_RETRIES", "5")) # Maximum number of consecutive failed login attempts 
    
    def __init__(self, crud_operations: CRUDOperations):
        self.crud_operations = crud_operations
        # self.MAX_PASSWORD_RETRIES = int(Env().str("MAX_PASSWORD_RETRIES", "5")) # Maximum number of consecutive failed login attempts 
        self.PASSWORD_RETRIES_TIME_WINDOW_MINUTES = int(Env().str("PASSWORD_RETRIES_TIME_WINDOW_MINUTES", "10"))
        
    def get_administrator_by_id(self, admin_id: int) -> Administrator:
        """
        Retrieve an administrator by ID.
        """
        return self.crud_operations.get_administrator(admin_id) # Check if the admin exists. Raises an exception if not found.
    
    def get_administrator_by_username(self, username: str) -> Administrator:
        """
        Retrieve an administrator by username.
        """
        return self._get_admin_by_username(username) # Check if the admin exists. Raises an exception if not found.


    def create_administrator(self, admin_data: dict) -> Administrator:
                    
        # Generate a salt
        salt = os.urandom(16).hex()
        raw_password = admin_data["password_hash"] # Extract the raw password from the data
        # Hash the password with the salt
        password_hash = self.hash_password(raw_password, salt)
        admin_data["password_hash"] = password_hash # Replace the raw password with the hashed password
        admin_data["salt"] = salt

        isValid, msg = validate_administrator_data(admin_data, True)
        if not isValid:
            raise InvalidAdministratorDataException(msg)

        return self.crud_operations.create_administrator(admin_data["username"], password_hash, salt)

    def update_administrator(self, admin_id: int, update_data: dict) -> Administrator:
        """
        Update an administrator's details.
        """
        isValid, msg = validate_administrator_data(update_data, False)
        if not isValid:
            raise InvalidAdministratorDataException(msg)
        return self.crud_operations.update_administrator(admin_id, update_data)

    def delete_administrator(self, admin_id: int) -> None:
        """
        Delete an administrator record.
        """
        self.crud_operations.delete_administrator(admin_id)

    def get_all_administrators(self) -> List[Administrator]:
        """
        Retrieve all administrators.
        """
        return self.crud_operations.get_administrators_by_filters({})

    # Security methods
    def verify_login_credentials(self, username: str, password: str) -> Optional[Administrator]:
        """
        Verify login credentials for an administrator.
        """
        admin = self._get_admin_by_username(username) # Check if the admin exists. Raises an exception if not found.
        if admin and not admin.account_locked:
            if self.verify_password(admin.password_hash, password, admin.salt):
                # Reset login failure counters on successful login
                self.reset_login_failure_counters(admin.id)
                return admin
            else:
                # Increment login failure counters
                self.increment_login_failure_counter(admin.id)
        return None
    
    def increment_login_failure_counter(self, admin_id: int) -> None:
        """
        Increment the consecutive_failed_logins counter and set failed_login_starttime.
        Lock the account if necessary, considering the retry time window.
        """
        admin = self._get_admin_by_id(admin_id) # Check if the admin exists. Raises an exception if not found.
        current_time = datetime.now(timezone.utc)  # Use timezone-aware datetime
        current_count = admin.consecutive_failed_logins
        time_window = timedelta(minutes=self.PASSWORD_RETRIES_TIME_WINDOW_MINUTES)  # Configure this as needed

        # Check if the current attempt is outside the retry time window
        if admin.failed_login_starttime:
            admin.failed_login_starttime = admin.failed_login_starttime.replace(tzinfo=timezone.utc) # Ensure timezone-aware datetime
            time_since_first_failure = current_time - admin.failed_login_starttime

            if time_since_first_failure > time_window:
                # Reset the counter and starttime if outside the retry window
                update_data = {
                    "consecutive_failed_logins": 1,  # Start fresh with the current failed attempt
                    "failed_login_starttime": current_time
                }
            else:
                # Increment the counter if within the retry window
                current_count += 1
                update_data = {"consecutive_failed_logins": current_count}
        else:
            # First failed attempt within a new window
            update_data = {
                "consecutive_failed_logins": 1,
                "failed_login_starttime": current_time
            }

        # Lock account if the failed attempts reach the threshold
        if current_count >= self.MAX_PASSWORD_RETRIES:
            update_data["account_locked"] = True

        self.crud_operations.update_administrator(admin_id, update_data)


    def reset_login_failure_counters(self, admin_id: int) -> None:
        """
        Reset the consecutive_failed_logins counter and failed_login_starttime.
        """
        update_data = {
            "consecutive_failed_logins": 0,
            "failed_login_starttime": None
        }
        self.crud_operations.update_administrator(admin_id, update_data)
    
    def hash_password(self, password: str, salt: str) -> str:
        """
        Hash a password with a salt using SHA-256.
        """
        return hashlib.sha256(f'{salt}:{password}'.encode('utf-8')).hexdigest()

    def verify_password(self, stored_password_hash: str, provided_password: str, salt: str) -> bool:
        """
        Verify a provided password against the stored password hash using the salt.
        """
        return stored_password_hash == self.hash_password(provided_password, salt)

        
    def unlock_administrator_account(self, admin_id: int) -> None:
        """
        Unlock an administrator's account, resetting the lock status and failure counters.
        """
        self._get_admin_by_id(admin_id) # Check if the admin exists. Raises an exception if not found.
        update_data = {
            "account_locked": False,
            "consecutive_failed_logins": 0,
            "failed_login_starttime": None
        }
        self.crud_operations.update_administrator(admin_id, update_data)

    def lock_administrator_account(self, admin_id: int) -> None:
        """
        Lock an administrator's account after too many consecutive login failures.
        """
        self._get_admin_by_id(admin_id) # Check if the admin exists. Raises an exception if not found.
        update_data = {"account_locked": True}
        self.crud_operations.update_administrator(admin_id, update_data)


    def _get_admin_by_id(self, admin_id: int) -> Administrator:
        admin = self.crud_operations.get_administrator(admin_id)
        if not admin:
            raise AdministratorNotFoundException(f"Administrator with ID {admin_id} not found.")
        return admin

    def _get_admin_by_username(self, username: str) -> Administrator:
        """
        Retrieve an administrator by username.
        """
        admin = self.crud_operations.get_administrator_by_username(username)
        if not admin:
            raise AdministratorNotFoundException(f"Administrator with Isername {username} not found.")
        return admin
