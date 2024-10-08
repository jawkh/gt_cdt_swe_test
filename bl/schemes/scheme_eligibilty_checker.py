# Copyright (c) 2024 by Jonathan AW
# This class is a concrete implementation of the BaseEligibility strategy. It provides behavior for checking eligibility and calculating benefits that are specific to an associated scheme.

""" 
Summary: The SchemeEligibilityChecker class acts as a context that holds a specific scheme and its corresponding eligibility strategy. 

Design Pattern: 

1. Strategy Pattern:
- The SchemeEligibilityChecker class uses the BaseEligibility strategy to determine the eligibility of an applicant for a specific scheme. This allows for flexibility in defining different eligibility criteria for various schemes.

2. Encapsulation:
- The class encapsulates the scheme and its eligibility definition, providing a clean interface for checking eligibility and calculating benefits for applicants.

3. Dependency Injection:
- The class takes the scheme and its eligibility definition as dependencies, promoting separation of concerns and testability.

4. Clear Naming and Documentation:
- The class name and method names are clear and descriptive, enhancing code readability and maintainability.

5. Type Annotations:
- The use of type annotations for method arguments and return types improves code readability and type safety.

6. Single Responsibility Principle (SRP):
- The class focuses on checking eligibility and calculating benefits for a specific scheme, adhering to the SRP.

7. Context Pattern:
- The SchemeEligibilityChecker class acts as a context for checking eligibility, providing a consistent interface for different schemes.

8. Readability and Maintainability:
- The class structure and method names are well-organized, making the code easy to understand and maintain.
    
"""
# scheme_eligibilty_checker.py
from dal.models import Scheme, Applicant
from bl.schemes.base_eligibility import BaseEligibility
from typing import List, Dict, Any
class SchemeEligibilityChecker:
    """
    Context class for checking eligibility for various schemes using a provided eligibility strategy.
    """

    def __init__(self, scheme: Scheme, eligibility_definition: BaseEligibility):
        """
        Initialize with a scheme and its associated eligibility definition.
        """
        self.scheme = scheme
        self.eligibility_definition = eligibility_definition

    def _check_eligibility(self, applicant: Applicant) -> tuple[bool, str]:
        """
        Check if the applicant is eligible for the scheme using the eligibility definition.
        """
        is_eligible, message = self.eligibility_definition.check_eligibility(applicant)
        return is_eligible, message

    def _calculate_benefits(self, applicant: Applicant) -> List[Dict[str, Any]]:
        """
        Calculate the benefits the applicant is eligible for under the scheme.
        """
        if self._check_eligibility(applicant)[0]:
            return self.eligibility_definition.calculate_benefits(applicant)
        return []
