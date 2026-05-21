import L from 'leaflet';

let map = null;

function getColor(count) {
    switch (true) {
        case count > 109: return '#800026';
        case count > 73:  return '#BD0026';
        case count > 37:  return '#E31A1C';
        case count > 1:   return '#FC4E2A';
        default:          return '#FD8D3C';
    }
}

export function initAttackerMap(attackerData) {
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) return;

    if (map === null) {
        map = L.map(mapContainer, { center: [20, 0], zoom: 2, minZoom: 1.5 });
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);      
    }

    if (attackerData && Array.isArray(attackerData)) {
        attackerData.forEach(row => {
            L.circleMarker([row.lat, row.lon], {
                radius: Math.min(row.count * 0.3, 30),
                color: getColor(row.count),
                fillColor: getColor(row.count),   
                fillOpacity: 0.5,
                weight: 1
            })
            .addTo(map)
            .bindPopup(`<b>IP:</b> ${row.ip}<br><b>Total Attacks:</b> ${row.count}`);
        });
    }
}
