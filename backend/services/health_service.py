class HealthService:
    @staticmethod
    def basic_vaccine_check(*, rabies_ok: bool, combo_ok: bool) -> bool:
        return bool(rabies_ok and combo_ok)

