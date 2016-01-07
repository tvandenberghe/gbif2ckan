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
    'd1f6b74b-1d53-44db-bed5-d08497095900': 'http://www.marinespecies.org/images/banner1.jpg'
}

# k: GBIF-returned name
# v: displayed, human-friendly name
DATASET_TYPES = {
    'CHECKLIST': 'Checklist',
    'OCCURRENCE': 'Occurrence',
    'SAMPLING_EVENT': 'Sampling Event'
}