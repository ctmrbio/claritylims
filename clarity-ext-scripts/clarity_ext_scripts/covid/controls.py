from clarity_ext_scripts.covid.utils import UniqueBarcodeGenerator

controls_barcode_generator = UniqueBarcodeGenerator("x")


class Controls(object):
    MGI_NEGATIVE_CONTROL = 1
    MGI_POSITIVE_CONTROL = 2
    NEGATIVE_WATER_CONTROL = 3
    POSITIVE_PLASMID_CONTROL = 4
    POSITIVE_VIRUS_CONTROL = 5
    NEGATIVE_VIRCON_CONTROL = 6

    # These controls are built in clarity control types, the others are real samples:
    NEGATIVE_PCR_CONTROL = 30
    POSITIVE_PCR_CONTROL = 31

    ALL = {
        MGI_NEGATIVE_CONTROL,
        MGI_POSITIVE_CONTROL,
        NEGATIVE_VIRCON_CONTROL,
        NEGATIVE_WATER_CONTROL,
        POSITIVE_PLASMID_CONTROL,
        POSITIVE_VIRUS_CONTROL,

        NEGATIVE_PCR_CONTROL,
        POSITIVE_PCR_CONTROL,
    }

    MAP_FROM_READABLE_TO_KEY = {
        "MGI Negative Control": MGI_NEGATIVE_CONTROL,
        "MGI Positive Control": MGI_POSITIVE_CONTROL,
        "Negative Vircon Control": NEGATIVE_VIRCON_CONTROL,
        "Negative Water Control": NEGATIVE_WATER_CONTROL,
        "Positive Plasmid Control": POSITIVE_PLASMID_CONTROL,
        "Positive Virus Control": POSITIVE_VIRUS_CONTROL,

        "Negative PCR Control": NEGATIVE_PCR_CONTROL,
        "Positive PCR Control": POSITIVE_PCR_CONTROL,
    }

    MAP_FROM_KEY_TO_ABBREVIATION = {
        MGI_NEGATIVE_CONTROL: "mgi-neg",
        MGI_POSITIVE_CONTROL: "mgi-pos",
        NEGATIVE_VIRCON_CONTROL: "vir-neg",
        NEGATIVE_WATER_CONTROL: "water",
        POSITIVE_PLASMID_CONTROL: "pla-pos",
        POSITIVE_VIRUS_CONTROL: "vir-pos",

        NEGATIVE_PCR_CONTROL: "pcr-neg",
        POSITIVE_PCR_CONTROL: "pcr-pos",
    }
