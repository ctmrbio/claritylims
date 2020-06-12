# -*- coding: utf-8 -*-

import os
import yaml
import logging
import codecs
import base64
import lxml
from lxml import objectify
import lxml.etree as ET
from suds.client import Client
from suds.xsd.doctor import ImportDoctor, Import

logger = logging.getLogger(__name__)


"""
A client for the SmiNet site


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
    child_element.text = unicode(value)  # Must always be cast to string


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


class Gender(object):
    MALE = "m"
    FEMALE = "k"
    UNKNOWN = "o"

    ALL = [MALE, FEMALE, UNKNOWN]


def SexType(python_string):
    """
    Avser patientens kön ('o'/'O' = Okänt).
    """
    if python_string.lower() not in Gender.ALL:
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


COUNTY_STOCKHOLM = "Stockholm"
COUNTY_UPPSALA = "Uppsala"
COUNTY_SODERMANLAND = "Sodermanland"
COUNTY_OSTERGOTLAND = "Ostergotland"
COUNTY_JONKOPING = "Jonkoping"
COUNTY_KRONOBERG = "Kronoberg"
COUNTY_KALMAR = "Kalmar"
COUNTY_GOTLAND = "Gotland"
COUNTY_BLEKINGE = "Blekinge"
COUNTY_SKANE = "Skane"
COUNTY_HALLAND = "Halland"
COUNTY_VASTRAGOTALAND = "Vastragotaland"
COUNTY_VARMLAND = "Varmland"
COUNTY_OREBRO = "Orebro"
COUNTY_VASTMANLAND = "Vastmanland"
COUNTY_DALARNA = "Dalarna"
COUNTY_GAVLEBORG = "Gavleborg"
COUNTY_VASTERNORRLAND = "Vasternorrland"
COUNTY_JAMTLAND = "Jamtland"
COUNTY_VASTERBOTTEN = "Vasterbotten"
COUNTY_NORRBOTTEN = "Norrbotten"


MAP_COUNTY_CODE_TO_NAME = {
    "AB": COUNTY_STOCKHOLM,
    "C": COUNTY_UPPSALA,
    "D": COUNTY_SODERMANLAND,
    "E": COUNTY_OSTERGOTLAND,
    "F": COUNTY_JONKOPING,
    "G": COUNTY_KRONOBERG,
    "H": COUNTY_KALMAR,
    "I": COUNTY_GOTLAND,
    "K": COUNTY_BLEKINGE,
    "M": COUNTY_SKANE,
    "N": COUNTY_HALLAND,
    "O": COUNTY_VASTRAGOTALAND,
    "S": COUNTY_VARMLAND,
    "T": COUNTY_OREBRO,
    "U": COUNTY_VASTMANLAND,
    "W": COUNTY_DALARNA,
    "X": COUNTY_GAVLEBORG,
    "Y": COUNTY_VASTERNORRLAND,
    "Z": COUNTY_JAMTLAND,
    "AC": COUNTY_VASTERBOTTEN,
    "BD": COUNTY_NORRBOTTEN,

    "OB": COUNTY_VASTRAGOTALAND,
    "OG": COUNTY_VASTRAGOTALAND,
    "OS": COUNTY_VASTRAGOTALAND,
    "OT": COUNTY_VASTRAGOTALAND,
}


def CountyType(python_string):
    """
    Avser smittskyddsläkarens landstingsbokstav.
    """
    if python_string not in MAP_COUNTY_CODE_TO_NAME.keys():
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


# NOTE: These are our translations of the status in the xsd StatusType documentation, which is in
# Swedish. Might be inaccurate.


class StatusType(object):
    """
    Original: Avser en anmälans status. Förklaring: 1. Slutsvar. 2. Komplettering kommer.
    3. Makulering av en tidigare anmälan. 4. Komplettering av en tidigare anmälan.
    """

    FINAL_RESPONSE = 1
    COMPLEMENTARY_DATA_PENDING = 2
    REVOCATION_OF_PREVIOUS_REPORT = 3
    COMPLEMENTARY_DATA = 4

    ALL = [FINAL_RESPONSE,
           COMPLEMENTARY_DATA_PENDING,
           REVOCATION_OF_PREVIOUS_REPORT,
           COMPLEMENTARY_DATA]

    def __init__(self, status):
        if status not in self.ALL:
            raise SmiNetValidationError("The status {} is not in the list of accepted statuses"
                                        .format(status))
        self.value = status


class SampleMaterial(object):
    """
    Avser undersökningsmatrial. (Notera att det är tillåtet att byta ut 'å' och 'ä' mot 'a'
    samt att 'ö' kan bytas ut mot 'o'. Detta alternativ finns om det skulle bli problem med
    valideringen pga konstigheter i teckentabeller.)
    """

    OTHER = "Annat"
    BIO = "Bio"
    BLOD = "Blod"
    BRONK = "Bronk"
    FECES = "Feces"
    LIKV = "Likv"
    LYMF = "Lymf"
    NFARY = "Nfary"
    NASA = "Nasa"
    PLEUR = "Pleur"
    SEKR = "Sekr"
    SERUM = "Serum"
    SPUT = "Sput"
    SVALG = "Svalg"
    SAR = "Sar"
    URIN = "Urin"
    VSK = "VSK"
    LED = "Led"
    PERIK = "Perik"
    FOST = "Fost"
    ASCI = "Asci"
    MELOR = "Melor"
    URET = "Uret"
    RECT = "Rect"
    CERV = "Cerv"
    VAGSEK = "VagSek"
    ASP = "Asp"
    BLODSR = "Blodsr"
    CERVUR = "Cervur"
    INFART = "Infart"
    NSP = "Nsp"
    PERIN = "Perin"
    POOLAT = "Poolat"
    SALIV = "Saliv"
    VAGUR = "Vagur"
    OGON = "Ogon"
    ORON = "Oron"

    ALL = [OTHER, BIO, BLOD, BRONK, FECES, LIKV,
           LYMF, NFARY, NASA, PLEUR, SEKR, SERUM,
           SPUT, SVALG, SAR, URIN, VSK, LED,
           PERIK, FOST, ASCI, MELOR, URET, RECT,
           CERV, VAGSEK, ASP, BLODSR, CERVUR, INFART,
           NSP, PERIN, POOLAT, SALIV, VAGUR,
           OGON, ORON]

    def __init__(self, value):
        if value not in self.ALL:
            raise SmiNetValidationError(
                "Material type not supported: {}".format(value))
        self.value = value


#####
# Complex types


class SmiNetComplexType(object):
    def to_element(self, element_name="element"):
        raise NotImplementedError()

    def __str__(self):
        return ET.tostring(self.to_element(), pretty_print=True)


class Laboratory(SmiNetComplexType):
    def __init__(self, lab_number, lab_name):
        """
        :lab_number: Non-negative integer. Each lab that connects with "automatisk överföring" against
                     SmiNet gets a unique identification number
        :lab_name: Name of the laboratory exporting the file. Max 255 characters.
        """
        self.lab_number = NonNegativeInteger(lab_number)
        self.lab_name = LongLimitedString(lab_name)

    def to_element(self, element_name="laboratory"):
        laboratory = ET.Element(element_name)
        add_child(laboratory, "labNumber", self.lab_number)
        add_child(laboratory, 'labName', self.lab_name)
        return laboratory


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
                 status, sample_id, sample_date_arrival, sample_material,
                 optional_reference=None,
                 sample_date_referral=None,
                 sample_free_text_lab=None,
                 sample_free_text_referral=None):
        """
        :status: Avser anmälans status.
        :sample_id: Laboratoriets unika provnummer.
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
        self.sample_id = ShortString(str(sample_id))
        self.sample_date_arrival = SmiNetDate(sample_date_arrival)
        self.sample_material = SampleMaterial(sample_material)
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
        add_child(element, "status", self.status.value)
        add_child(element, "sampleNumber", self.sample_id)
        add_child(element, "sampleDateArrival", self.sample_date_arrival)
        add_child(element, "sampleDateReferral", self.sample_date_referral)
        add_child(element, "sampleMaterial", self.sample_material.value)
        add_child(element, "optionalReference", self.optional_reference)
        add_child(element, "sampleFreeTextLab", self.sample_free_text_lab)
        add_child(element, "sampleFreeTextReferral",
                  self.sample_free_text_referral)
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


class Notification(SmiNetComplexType):

    SampleInfo = SampleInfo
    Doctor = Doctor
    ReferringClinic = ReferringClinic
    Patient = Patient

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


class SmiNetLabExport():
    """
    Creates a validated lab export as XML that is acceptable for the SmiNet endpoint.

    Those values that are constant for the time being are set as constants in this method.

    Original documentation in xsd: Rootelementet i xml-dokumentet.
    Varje exportfil (XML-fil) måste innehålla ett och endast ett sådant element.
    """

    # For convenience, all the types that make up an export are defined here:
    Laboratory = Laboratory
    Notification = Notification

    def __init__(self, created, laboratory, notification):
        self.created = created
        self.laboratory = laboratory
        self.notification = notification
        self.version = Version("4.0.0")

    def to_element(self, xsd_url):
        element = ET.Element('smiNetLabExport')

        # element.attrib['xmlns:xsi'] = ""
        element.attrib["{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation"] = xsd_url

        # # smiNetLabExport/version/version-number
        element.append(self.version)

        # # smiNetLabExport/dateTimeCreated
        date_time_created = ET.Element("dateTimeCreated")
        date_time_created.text = SmiNetDateTime(self.created)
        element.append(date_time_created)

        # # smiNetLabExport/laboratory
        element.append(self.laboratory.to_element())
        element.append(self.notification.to_element())
        return element

    def to_document(self, xsd_url):
        """
        Creates an XML string representation that should be accepted by SmiNet
        """
        export = self.to_element(xsd_url)
        return ET.tostring(export, pretty_print=True, encoding="ISO-8859-1")


class SmiNetError(Exception):
    pass


class SmiNetValidationError(SmiNetError):
    pass


class SmiNetRequestError(SmiNetError):
    pass


class SmiNetClient(object):

    SMINET_ENVIRONMENT_STAGE = "stage"
    SMINET_ENVIRONMENT_PROD = "prod"

    def __init__(self, config):
        """
        :config: A configuration object of type SmiNetConfig
        """

        self.config = config
        self._soap_client = None

        if config.environment == self.SMINET_ENVIRONMENT_STAGE:
            self.url = "https://stage.sminet.se/sminetlabxmlzone/services/SmiNetLabXmlZone"
            self.xsd_url = "http://stage.sminet.se/xml-schemas/SmiNetLabExport.xsd"
            self.wsdl_url = "https://stage.sminet.se/sminetlabxmlzone/services/SmiNetLabXmlZone?wsdl"
        elif config.environment == self.SMINET_ENVIRONMENT_PROD:
            self.url = "https://sminet.se/sminetlabxmlzone/services/SmiNetLabXmlZone"
            self.xsd_url = "http://sminet.se/xml-schemas/SmiNetLabExport.xsd"
            self.wsdl_url = "https://sminet.se/sminetlabxmlzone/services/SmiNetLabXmlZone?wsdl"

    @property
    def soap_client(self):
        if self._soap_client is None:
            imp = Import('http://schemas.xmlsoap.org/soap/encoding/')
            doctor = ImportDoctor(imp)
            self._soap_client = Client(self.wsdl_url,
                                       doctor=doctor)
        return self._soap_client

    def is_supported_county_code(self, county_code):
        return county_code in MAP_COUNTY_CODE_TO_NAME.keys()

    def create(self, sminet_lab_export, file_name):
        """
        Creates the entry in SmiNet

        :export: An instance of SmiNetLabExport
        :file_name: Name of the file in SmiNet's database
        """
        logger.info("Creating a request at SmiNet")
        doc = sminet_lab_export.to_document(self.xsd_url)
        self._send_file(doc, file_name)

    def _parse_xml(self, xml):
        """
        Returns a Python object from an XML response string"
        """
        xml = codecs.encode(xml, "utf-8")
        obj = objectify.fromstring(xml)
        return obj

    def _send_file(self, xml_file, file_name):
        """
        Sends an XML document to SmiNet.

        Raises a SmiNetRequestError if the return code is not zero.

        :xml_file: A valid xml document as a string. Use SmiNetLabExport to generate
        a valid document.
        :file_name: The name of the file in SmiNet
        """
        base64encoded = base64.b64encode(xml_file)

        resp = self.soap_client.service.submitFile(
            self.config.username, self.config.password, file_name, base64encoded)
        resp = self._parse_xml(resp)

        if resp.returnCode != 0:
            raise SmiNetRequestError(resp.message)

    def validate(self, xml):
        """
        Validates an XML contract against the xsd SmiNet provides
        """
        xml_validator = lxml.etree.XMLSchema(
            file="http://stage.sminet.se/xml-schemas/SmiNetLabExport.xsd")
        is_valid = xml_validator.validate(xml)

        if not is_valid:
            raise SmiNetValidationError(
                "Not able to validate xml against the xsd file")


class SmiNetConfig(object):
    DEFAULT_PATH_ETC = "/etc/sminet_client/sminet_client.config"
    DEFAULT_PATH_USER = "~/.config/sminet_client/sminet_client.config"

    def __init__(self, sminet_username,
                 sminet_password,
                 sminet_proxy,
                 sminet_environment,
                 sminet_lab_name,
                 sminet_lab_number,
                 **kwargs):
        """
        Creates a configuration file that's valid for this SmiNet client.

        Searches the search paths for a valid configuration file

        :sminet_username: The username
        :sminet_password: The password
        :sminet_environment: The environment, e.g. SmiNetClient.SMINET_ENVIRONMENT_STAGE
        :proxy: Proxy info if the service is only accessible via a proxy
        :lab_name: The name of your lab
        :lab_number: The name of your lab
        """
        self.username = sminet_username
        self.password = sminet_password
        self.proxy = sminet_proxy
        self.environment = sminet_environment
        self.lab_name = sminet_lab_name
        self.lab_number = sminet_lab_number

    @classmethod
    def create_from_search_paths(cls, paths=None):
        if not paths:
            paths = [cls.DEFAULT_PATH_ETC, cls.DEFAULT_PATH_USER]

        for path in paths:
            path = os.path.expanduser(path)
            if os.path.exists(path):
                with open(path, "r") as f:
                    config = yaml.safe_load(f)
                    return cls(**config)
        raise SmiNetConfigNotFoundError(
            "No config file found in {}".format(paths))


class SmiNetConfigNotFoundError(Exception):
    pass
