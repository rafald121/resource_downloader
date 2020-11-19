class ResourceGenerationStatusChoices():

    STARTED_GENERATION = 0
    STARTED_GENERATION_LABEL = 'Started generation'
    GENERATED = 1
    GENERATED_LABEL = 'Generated'
    ERROR = 10
    ERROR_LABEL = 'Error'

    choices = (
        (STARTED_GENERATION, STARTED_GENERATION_LABEL),
        (GENERATED, GENERATED_LABEL),
        (ERROR, ERROR_LABEL),
    )

    @classmethod
    def get_label_for_choice(cls, choice):
        return cls.get_choices_dict()[choice]

    @classmethod
    def get_choices_dict(cls):
        return {
            val[0]: val[1] for val in cls.choices
        }