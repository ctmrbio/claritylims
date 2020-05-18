# -*- coding: utf-8 -*-

import lxml.etree as ET
import datetime

"""
A Python client for the SmiNet site


NOTE: Some of the documentation is in Swedish. In those cases, it has been copied directly from
http://stage.sminet.se/xml-schemas/SmiNetLabExport.xsd
"""


def add_child(parent, elementName, value, validator=None):
    """
    Adds a simple child element that only has value in the text.
    Skips adding it if value is None.
    """
    if value is None:
        return
    child_element = ET.SubElement(parent, elementName)
    if validator:
        value = validator(value)
    child_element.text = str(value)  # Must always be cast to string


####
# Simple types and validators

def IdType(python_string):
    """
    Avser personnummer eller i känsliga ärenden en rikskod, annat nummer alt. sammordningsnummer.
    Fyra olika format godkänns:

    1) (Personnummer) 12 siffror och 13 tecken ('-' avgränsare), exempel: "19671208-1123".
    2) (Rikskod) Exempel: "1967-1123" ('-' avgränsare).
    3) (annat nummer) Övriga format (max 20 tecken).
    4) (samordningsnummer) Formatet (YY)YYMMDD-XXXX där DD är ett tal mellan 61-91 och
       där kontrollsiffran stämmer på samma vis som för personnummer.
    """
    if len(python_string) > 20:
        raise SmiNetValidationError(
            "The ID can not be longer than 20 characters")
    return python_string


def SexType(python_string):
    """
    Avser patientens kön ('o'/'O' = Okänt).
    """
    if python_string.lower() not in ["m", "k", "o"]:
        raise SmiNetValidationError(
            "Unknown sex type {}".format(python_string))
    return python_string


def DiagnosticMethod(python_string):
    """
    Avser diagnostisk metod enligt kriterielista i Epidaktuellt 8/95. (Notera att flera
    DiagnosticMethod listade efter varandra är tillåtna.)
    """
    if python_string not in ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "M", "Z"]:
        raise SmiNetValidationError(
            "Diagnostic method not defined: {}".format(python_string))
    return python_string


def CountyType(python_string):
    """
    Avser smittskyddsläkarens landstingsbokstav.
    """
    if python_string not in ["AB", "C", "D", "E", "F", "G", "H", "I", "K", "M",
                             "N", "O", "OB", "OG", "OS", "OT", "S", "T", "U", "W",
                             "X", "Y", "Z", "AC", "BD"]:
        raise SmiNetValidationError(
            "Unknown county code {}".format(python_string))
    return python_string


def NonNegativeInteger(num):
    """
    Ensures that the number is non negative
    """
    if num < 0:
        raise SmiNetValidationError("A non-negative integer is required")
    return num


def SmiNetDate(python_date):
    """
    Date as a string in the format `YYYY-MM-DD`

    Original xsd documentation: SmiNetLabExporters datumformat (ÅÅÅÅ-MM-DD).
    """
    return python_date.strftime("%Y-%m-%d")


def SmiNetDateTime(python_date):
    """
    Datetime as a string in the format `YYYY-MM-DD HH:MM:SS`

    Original xsd documentation: SmiNetLabExporters datum- och tidformat (ÅÅÅÅ-MM-DD TT:MM:SS).
    """
    return python_date.strftime("%Y-%m-%d %H:%M:%S")


def validate_string(python_string, max_len):
    """
    Helper method for the different string types
    """
    if len(python_string) > max_len:
        raise SmiNetValidationError(
            "The string is longer than {} characters".format(max_len))
    return python_string


def ShortLimitedString(python_string):
    """
    A string that's max 15 characters long

    Original xsd documentation: En sträng, max 15 tecken lång.
    """
    return validate_string(python_string, 15)


def ShortString(python_string):
    """
    A string that's max 25 characters long

    Original xsd documentation: En sträng, max 25 tecken lång.
    """
    return validate_string(python_string, 25)


def LimitedString(python_string):
    """
    A string that's max 40 characters long

    Original xsd documentation: En sträng, max 40 tecken lång.
    """
    return validate_string(python_string, 40)


def LongLimitedString(python_string):
    """
    A string that's max 255 characters long

    Original xsd documentation: En sträng, max 255 tecken lång.
    """
    return validate_string(python_string, 255)


def FreeText(python_string):
    """
    A string that's max 1500 characters long

    Original xsd documentation: En sträng, max 1500 tecken lång.
    """
    return validate_string(python_string, 1500)


def Version(version_number):
    element = ET.Element('version')
    add_child(element, "version-number", version_number, ShortString)
    return element


def Laboratory(lab_number, lab_name):
    """
    :lab_number: Non-negative integer. Each lab that connects with "automatisk överföring" against
                 SmiNet gets a unique identification number
    :lab_name: Name of the laboratory exporting the file. Max 255 characters.
    """
    laboratory = ET.Element("laboratory")
    add_child(laboratory, "labNumber", lab_number, NonNegativeInteger)
    add_child(laboratory, 'labName', lab_name, LongLimitedString)

    return laboratory


# NOTE: These are our translations of the status in the xsd StatusType documentation, which is in
# Swedish. Might be inaccurate.
STATUS_FINAL_RESPONSE = 1
STATUS_COMPLEMENTARY_DATA_PENDING = 2
STATUS_REVOCATION_OF_PREVIOUS_REPORT = 3
STATUS_COMPLEMENTARY_DATA = 4


def StatusType(status):
    """
    Original: Avser en anmälans status. Förklaring: 1. Slutsvar. 2. Komplettering kommer.
    3. Makulering av en tidigare anmälan. 4. Komplettering av en tidigare anmälan.
    """
    if status not in [STATUS_FINAL_RESPONSE,
                      STATUS_COMPLEMENTARY_DATA_PENDING,
                      STATUS_REVOCATION_OF_PREVIOUS_REPORT,
                      STATUS_COMPLEMENTARY_DATA]:
        raise SmiNetValidationError("The status {} is not in the list of accepted statuses"
                                    .format(status))
    return status


def SampleMaterialType(material_type):
    """
    Avser undersökningsmatrial. (Notera att det är tillåtet att byta ut 'å' och 'ä' mot 'a'
    samt att 'ö' kan bytas ut mot 'o'. Detta alternativ finns om det skulle bli problem med
    valideringen pga konstigheter i teckentabeller.)
    """

    supported = ["Annat" "Bio", "Blod", "Bronk", "Feces", "Likv", "Lymf",
                 "Nfary", "Nasa", "Pleur", "Sekr", "Serum", "Sput", "Svalg", "Sar",
                 "Urin", "VSK", "Led", "Perik", "Fost", "Asci", "Melor", "Uret",
                 "Rect", "Cerv", "VagSek", "Asp", "Blodsr", "Cervur", "Infart", "Nsp",
                 "Perin", "Poolat", "Saliv", "Vagur", "Ogon", "Oron"]
    if material_type not in supported:
        raise SmiNetValidationError(
            "Material type not supported: {}".format(material_type))
    return material_type


#####
# Complex types


class SmiNetComplexType(object):
    def to_element(self, element_name="element"):
        raise NotImplementedError()

    def __str__(self):
        return ET.tostring(self.to_element(), pretty_print=True)


class ReferringClinic(SmiNetComplexType):
    def __init__(self, referring_clinic_name, referring_clinic_address,
                 referring_clinic_county, referring_doctor=None):
        """
        :referring_clinic_name: Den insändande klinikens namn.
        :referring_clinic_address: Den insändande klinikens adress.
        :referring_clinic_county: Det landsting som den insändande kliniken tillhör.
        :referring_doctor: Information om den läkare som remitterade provet, på angiven klinik.
        """
        self.referring_clinic_name = LongLimitedString(referring_clinic_name)
        self.referring_clinic_address = LongLimitedString(
            referring_clinic_address)
        self.referring_clinic_county = CountyType(referring_clinic_county)
        self.referring_doctor = referring_doctor

    def to_element(self, element_name="referringClinic"):
        element = ET.Element(element_name)
        add_child(element, "referringClinicName", self.referring_clinic_name)
        add_child(element, "referringClinicAddress",
                  self.referring_clinic_address)
        add_child(element, "referringClinicCounty",
                  self.referring_clinic_county)
        if self.referring_doctor:
            element.append(self.referring_doctor.to_element("referringDoctor"))
        return element


class Doctor(SmiNetComplexType):
    def __init__(self, name=None, office_phone_number=None):
        """
        Has information about a doctor, either the responsible doctor at the lab that's sending the
        information or the doctor treating the patient at the clinic.

        Original xsd documentation: DoctorType innehåller information om en läkare, antingen
        ansvarig läkare på det inskickande laboratoriet eller behandlande läkare på kliniken.
        """
        self.name = LimitedString(name) if name else None
        self.office_phone_number = LimitedString(
            office_phone_number) if office_phone_number else None

    def to_element(self, element_name="doctor"):
        element = ET.Element(element_name)
        add_child(element, "name", self.name)
        add_child(element, "officePhoneNumber", self.office_phone_number)
        return element


class SampleInfo(SmiNetComplexType):
    def __init__(self,
                 status, sample_number, sample_date_arrival, sample_material,
                 optional_reference=None,
                 sample_date_referral=None,
                 sample_free_text_lab=None,
                 sample_free_text_referral=None):
        """
        :status: Avser anmälans status.
        :sample_number: Laboratoriets unika provnummer.
        :sample_date_arrival: Det datum som provet ankom till laboratoriet.
        :sample_date_referral: Det datum som patienten provtogs.
        :sample_material: Avser undersökningsmatrial.
        :optional_reference: Valfri lokal referens som skickas tillbaka med kvittot för spårbarhet.
        :sample_free_text_lab: LABORATORIETS eventuella kommentarer till provet.
        :sample_free_text_referral: PROVTAGERENS eventuella kommentarer till provet.

        NOTE: There is one additional value, `sentForReferenceBy` which we don't support here.
        Original: Översiktlig information om provet
        """
        self.status = StatusType(status)
        # Is a string according to the docs
        self.sample_number = ShortString(str(sample_number))
        self.sample_date_arrival = SmiNetDate(sample_date_arrival)
        self.sample_material = SampleMaterialType(sample_material)
        self.optional_reference = ShortLimitedString(
            optional_reference) if optional_reference else None
        self.sample_date_referral = SmiNetDate(
            sample_date_referral) if sample_date_referral else None
        self.sample_free_text_lab = FreeText(
            sample_free_text_lab) if sample_free_text_lab else None
        self.sample_free_text_referral = FreeText(
            sample_free_text_referral) if sample_free_text_referral else None

    def to_element(self, element_name="sampleInfo"):
        element = ET.Element(element_name)
        add_child(element, "status", self.status)
        add_child(element, "sampleNumber", self.sample_number)
        add_child(element, "sampleDateArrival", self.sample_date_arrival)
        add_child(element, "sampleDateReferral", self.sample_date_referral)
        add_child(element, "sampleMaterial", self.sample_material)
        add_child(element, "optionalReference", self.optional_reference)
        add_child(element, "sampleFreeTextLab", self.sample_free_text_lab)
        add_child(element, "sampleFreeTextReferral",
                  self.sample_free_text_referral)
        return element


class NotificationType(SmiNetComplexType):

    def __init__(self, sample_info, reporting_doctor, referring_clinic, patient, lab_result):
        """
        :sample_info: Översiktlig information om provet.
        :reporting_doctor: Information om, på laboratoriet, ansvarig läkare.
        :referring_clinic: Information om kliniken som provtog patienten och skickade
                           in provet till laboratoriet.
        :patient: Information om den provtagna patienten.
        :lab_result: Information om provresultatet.
        """
        self.sample_info = sample_info
        self.reporting_doctor = reporting_doctor
        self.referring_clinic = referring_clinic
        self.patient = patient
        self.lab_result = lab_result

    def to_element(self):
        element = ET.Element("notification")
        element.append(self.sample_info.to_element("sampleInfo"))
        element.append(self.reporting_doctor.to_element("reportingDoctor"))
        element.append(self.referring_clinic.to_element("referringClinic"))
        element.append(self.patient.to_element("patient"))
        element.append(self.lab_result.to_element("labResult"))
        return element


class LabDiagnosisType(SmiNetComplexType):
    def __init__(self, diagnose_in_code, diagnose_in_text):
        """
        :diagnose_in_code: Labdiagnosens SmiNet-kod
        :diagnose_in_text: Labdiagnosen i klartext
        """

        if diagnose_in_code not in [
            "Apato", "Banthr", "Bpertus", "Bruspp", "Campyl", "Cbotul", "Cburne", "Cdipht",
            "Cpsitt", "Cryspp", "Ctetan", "Ctrach", "Dengue", "Echspp", "EHEC", "ESBL", "ESBLCL",
            "ESBLC", "Ehisto", "Ftular", "Giarspp", "Gulafe", "HAV", "HBV", "HCV", "HDV", "HEV",
            "H5N1l", "Hinflu", "HIV", "HTLV1", "HTLV2", "ITypA", "ITypB", "Legspp", "Lepspp",
            "Lisspp", "Mbatyp", "Menin", "MERSC", "Morbil", "MRSA", "Mtuber", "Ngonor", "Nmenin",
            "Paroti", "Plaspp", "PNSP", "Poliov", "Puumal", "Rabies", "Rubell", "Sapo", "SARS",
            "SCOV2", "Salspp", "Shispp", "SParat", "Spneu", "Spyog", "STyphi", "TBE", "Tpalli",
            "Tspira", "Vchole", "VHF", "Vibspp",
                "VREfis", "VREfum", "Yenter", "Ypesti"]:
            raise SmiNetValidationError(
                "Unexpected diagnostic code: {}".format(diagnose_in_code))
        self.diagnose_in_code = diagnose_in_code
        self.diagnose_in_text = LongLimitedString(diagnose_in_text)

    def to_element(self, element_name="labDiagnosis"):
        element = ET.Element(element_name)
        add_child(element, "diagnoseInCode", self.diagnose_in_code)
        add_child(element, "diagnoseInText", self.diagnose_in_text)
        return element


class LabResult(SmiNetComplexType):
    """
    Avser diagnostisk metod.
    """

    def __init__(self, diagnostic_method, lab_diagnosis):
        """
        :diagnostic_method: Observera att det är SmiNet-koden för diagnostisk metod som
                            ska användas. 
        :lab_diagnosis: Viktig typningsinformation om provet, som till exempel eventuell
                        typningsinformation om sådan finns.  

        """
        self.diagnostic_method = DiagnosticMethod(diagnostic_method)
        self.lab_diagnosis = lab_diagnosis

    def to_element(self, element_name="labResult"):

        element = ET.Element(element_name)
        add_child(element, "diagnosticMethod", self.diagnostic_method)
        element.append(self.lab_diagnosis.to_element())
        return element


class Patient(SmiNetComplexType):
    """
    Information för att identifiera patienten.
    """

    def __init__(self, patient_id, patient_sex, patient_name=None, patient_age=None):
        """
        :patient_id: Tillåtna typer är personnummer, rikskod och reservkod
        :patient_sex: Patientens kön
        :patient_name: Patientens namn
        :patient_age: Patientens ålder
        """
        self.patient_id = IdType(patient_id)
        self.patient_sex = SexType(patient_sex)
        self.patient_name = LimitedString(patient_name)
        self.patient_age = NonNegativeInteger(
            patient_age) if patient_age else None

    def to_element(self, element_name="patient"):
        element = ET.Element(element_name)
        add_child(element, "patientId", self.patient_id)
        add_child(element, "patientSex", self.patient_sex)
        add_child(element, "patientName", self.patient_name)
        add_child(element, "patientAge", self.patient_age)
        return element


def SmiNetLabExport(created, notification):
    """
    Creates a validated lab export as XML that is acceptable for the SmiNet endpoint.

    Those values that are constant for the time being are set as constants in this method.

    Original documentation in xsd: Rootelementet i xml-dokumentet.
    Varje exportfil (XML-fil) måste innehålla ett och endast ett sådant element.
    """
    element = ET.Element('smiNetLabExport')  # TODO: xlmns and xsi

    # # smiNetLabExport/version/version-number
    element.append(Version("4.0.0"))

    # # smiNetLabExport/dateTimeCreated
    date_time_created = ET.Element("dateTimeCreated")
    date_time_created.text = SmiNetDateTime(created)
    element.append(date_time_created)

    # # smiNetLabExport/laboratory
    lab_number = 10  # TODO: Get this ID
    element.append(Laboratory(lab_number, "National Pandemic Center at KI"))

    element.append(notification.to_element())
    return element


def create_scov2_positive_lab_result():
    lab_diagnosis = LabDiagnosisType("SCOV2", "SARS-CoV-2 (covid-19)")
    return LabResult("C", lab_diagnosis)


def create_covid_request(created, sample_info, referring_clinic, patient):
    """
    Creates a request to SmiNet that's valid for the Covid project.

    :sample_info: An object created with the SampleInfo factory
    :referring_clinic: An object created with the ReferringClinic factory
    :patient: An object created with the Patient factory
    """

    reporting_doctor = Doctor("Lars Engstrand")
    notification = NotificationType(sample_info, reporting_doctor, referring_clinic, patient,
                                    create_scov2_positive_lab_result())

    contract = SmiNetLabExport(created, notification)

    return ET.tostring(contract, pretty_print=True, encoding="ISO-8859-1")


class SmiNetValidationError(Exception):
    pass
