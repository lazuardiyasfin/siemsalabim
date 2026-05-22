export function getColor(count) {
    switch (true) {
        case count > 109: return '#800026';
        case count > 73:  return '#BD0026';
        case count > 37:  return '#E31A1C';
        case count > 0:   return '#FC4E2A';
        default:          return '#FD8D3C';
    }
}