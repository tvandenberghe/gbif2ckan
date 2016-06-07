COUNTRY_CODE = "BE"  # The country we want to load the data for...

CKAN_INSTANCE_URL = "http://localhost:5000/"
ADMIN_API_KEY = "Type your CKAN API admin key here"

# Additional data (not from GBIF) used to populate the CKAN instance:

ORGANIZATION_LOGOS = {
    '37e82b90-1e21-11de-ab90-f72009d2669b': 'http://ias.biodiversity.be/pics/BBPf.png', # BeBIF provider
    '05c249d0-dfa0-11d8-b22e-b8a03c50a862': 'http://www.marinebiology.ugent.be/sites/marinebiology.ugent.be/files/public/images/logo/logo_marbiol_transp_150.gif',
    '1cd669d0-80ea-11de-a9d0-f1765f95f18b': 'https://www.inbo.be/sites/all/themes/bootstrap_inbo/img/inbo/logo.png',
    'a344ee9f-f1b7-4761-be2c-58ee6d741395': 'http://www.botanicgarden.be/PUBLIC/IMAGES/ICONS/Logo_UK_groen1_trans.gif',
    'e88c96a3-5884-4e51-a580-e417ca4c9eed': 'http://projects.biodiversity.be/openuprbins/static/img/logo_rbins.gif',
    '575c52b0-a742-11db-a6ff-b8a03c50a862': 'http://www.damiendelvaux.be/Tensor/Logo-AfricaMuseum.jpg',
    '576f00f2-c26c-41f7-991e-a37e07cbd3ec': 'https://www.ulb.ac.be/dre/com/docs/logo3lg.jpg',
    'd02b7f80-1b78-11dd-be3c-b8a03c50a862': 'https://upload.wikimedia.org/wikipedia/fr/thumb/3/34/Universit%C3%A9_de_Mons_%28logo%29.svg/langfr-640px-Universit%C3%A9_de_Mons_%28logo%29.svg.png',
    'd1f6b74b-1d53-44db-bed5-d08497095900': 'http://www.marinespecies.org/images/banner1.jpg',
    '4d3ceea8-5699-439d-a899-decac9cbbdac': 'https://www.natuurpunt.be/sites/default/files/images/inline/natuurpunt_logo_groen_.jpg',
    '6cb013c5-97ae-4541-a2f5-40e0d13c8242': 'http://www.hach.ulg.ac.be/cms/system/files/logo_coul_texte_blason_cadre_300.gif'
}

# k: GBIF-returned name
# v: displayed, human-friendly name
DATASET_INFO = {
    'CHECKLIST': {'name': 'Checklist', 'logo_url': 'https://dataset.readthedocs.org/en/latest/_static/dataset-logo.png'},
    'OCCURRENCE': {'name': 'Occurrence', 'logo_url': 'https://c1.staticflickr.com/3/2445/3919289329_b6760414a8_b_d.jpg'},
    'SAMPLING_EVENT': {'name': 'Sampling Event', 'logo_url': 'https://dataset.readthedocs.org/en/latest/_static/dataset-logo.png'},
    'METADATA': {'name': 'Metadata-only', 'logo_url': 'https://dataset.readthedocs.org/en/latest/_static/dataset-logo.png'}
}
