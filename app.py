from flask import Flask, jsonify
import swisseph as swe
from datetime import datetime

app = Flask(__name__)
swe.set_ephe_path('/app/swisseph/ephe')
def calculate_aspect(angle_diff):
    aspects = {
        'Conjunction': (0, 8),
        'Sextile': (60, 6),
        'Square': (90, 8),
        'Trine': (120, 8),
        'Opposition': (180, 8)
    }
    angle_diff = min(angle_diff, 360 - angle_diff)  # Ángulo menor
    for name, (target, orb) in aspects.items():
        if abs(angle_diff - target) <= orb:
            return name
    return None

@app.route('/sky', methods=['GET'])
def get_sky_map():
    now = datetime.utcnow()
    julday = swe.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)
    bodies = {
        'Sun': swe.SUN,
        'Moon': swe.MOON,
        'Mercury': swe.MERCURY,
        'Venus': swe.VENUS,
        'Mars': swe.MARS,
        'Jupiter': swe.JUPITER,
        'Saturn': swe.SATURN,
        'Uranus': swe.URANUS,
        'Neptune': swe.NEPTUNE,
        'Pluto': swe.PLUTO
    }
    signs = ['Aries', 'Tauro', 'Géminis', 'Cáncer', 'Leo', 'Virgo', 'Libra', 'Escorpio', 'Sagitario', 'Capricornio', 'Acuario', 'Piscis']
    sky_map = {}
    for name, body in bodies.items():
        data = swe.calc_ut(julday, body)
        longitude = data[0][0]  # Longitud eclíptica
        sign = signs[int(longitude // 30)]
        sky_map[name] = {'longitude': longitude, 'sign': sign}

    # Calcular aspectos
    aspects = {}
    for body1 in sky_map:
        for body2 in sky_map:
            if body1 < body2:  # Evitar duplicados
                diff = abs(sky_map[body1]['longitude'] - sky_map[body2]['longitude'])
                aspect = calculate_aspect(diff)
                if aspect:
                    aspects[f"{body1}-{body2}"] = aspect

    sky_map['aspects'] = aspects
    sky_map['timestamp'] = now.isoformat()
    return jsonify(sky_map)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
