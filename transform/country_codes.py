mapping = {
    ' NEZNANO': 'unknown',
    'Albanija': 'alb',
    'Avstralija': 'aus',
    'Avstrija': 'aut',
    'Azerbajdžan': 'aze',
    'Belgija': 'bel',
    'Bolgarija': 'bgr',
    'Bosna in Hercegovina': 'bih',
    'Češka': 'cze',
    'Črna Gora': 'mne',
    'Danska': 'dnk',
    'Dominikanska republika': 'dom',
    'Estonija': 'est',
    'Francija': 'fra',
    'Grčija': 'grc',
    'Hrvaška': 'hrv',
    'Italija': 'ita',
    'Kosovo': 'xkx',
    'Kuba': 'cub',
    'Latvija': 'lva',
    'Madžarska': 'hum',
    'Makedonija': 'mkd',
    'NAM': 'nam',
    'Nizozemska': 'nld',
    'Malta': 'mlt',
    'Maroko': 'mar',
    'Mehika': 'mex',
    'Mikronezija': 'fsm',
    'Nemčija': 'deu',
    'Pakistan': 'pak',
    'Poljska': 'pol',
    'Portugalska': 'prt',
    'Romunija': 'rou',
    'Ruska federacija': 'rus',
    'Slovaška': 'svk',
    'Slovenija': 'svn',
    'Španija': 'esp',
    'Srbija': 'srb',
    'Švedska': 'swe',
    'Švica': 'che',
    'Turčija': 'tur',
    'Ukrajina': 'ukr',
    'Združeno kraljestvo': 'gbr',
    'Združeno kraljestvo Velike Britanije in Severne Irske': 'gbr',
    'Združene države Amerike': 'usa',
    'Združeni Arabski Emirati': 'are',
}


def get_county_code(country_name: str):
    return mapping[country_name]
