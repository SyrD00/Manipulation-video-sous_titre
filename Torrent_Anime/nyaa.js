import AbstractSource from './abstract-source.js'

export default class NyaaSource extends AbstractSource {
  name = 'Nyaa.si'
  description = 'Anime torrents from Nyaa.si (robust version)'
  accuracy = 'High'
  config = {}

  /**
   * Recherche un seul épisode ou une série
   * @param {{ query: string }} options
   */
  async single({ query }) {
    let results = [];
    let page = 1;
    const maxPages = 3; // Nombre de pages à scraper pour limiter la charge

    while (page <= maxPages) {
      const url = `https://nyaa.si/?f=0&c=1_2&q=${encodeURIComponent(query)}&p=${page}`;
      const html = await fetch(url).then(r => r.text());

      // Chaque ligne <tr> du tableau de résultats
      const rowRegex = /<tr>([\s\S]*?)<\/tr>/g;
      let rowMatch;

      while ((rowMatch = rowRegex.exec(html)) !== null) {
        const row = rowMatch[1];

        // Titre
        const titleMatch = row.match(/<a href="\/view\/\d+" title="([^"]+)"/);
        if (!titleMatch) continue;
        const title = titleMatch[1];

        // Magnet
        const magnetMatch = row.match(/href="(magnet:\?xt=urn:btih:[^"]+)"/);
        if (!magnetMatch) continue;
        const magnet = magnetMatch[1];

        // Taille
        const sizeMatch = row.match(/<td class="text-center">([\d.]+\s(?:KiB|MiB|GiB|TiB))<\/td>/);
        const size = sizeMatch ? sizeMatch[1] : "N/A";

        // Seeders / Leechers
        const slMatch = row.match(/<td class="text-center">(\d+)<\/td>\s*<td class="text-center">(\d+)<\/td>/);
        const seeders = slMatch ? slMatch[1] : null;
        const leechers = slMatch ? slMatch[2] : null;

        // Date
        const dateMatch = row.match(/<td class="text-center" title="[^"]+">([^<]+)<\/td>/);
        const date = dateMatch ? dateMatch[1] : "N/A";

        // Uploader
        const uploaderMatch = row.match(/<td class="text-center"><a href="\/user\/[^"]+">([^<]+)<\/a><\/td>/);
        const uploader = uploaderMatch ? uploaderMatch[1] : "N/A";

        // Type de release (RAW, SUB, etc.)
        const typeMatch = row.match(/<td class="text-center">([A-Z]+)<\/td>/);
        const type = typeMatch ? typeMatch[1] : "N/A";

        results.push({ title, magnet, size, seeders, leechers, date, uploader, type });
      }

      // Si moins de 75 résultats sur la page, fin du scraping
      if (!html.includes('<tr>')) break;
      page++;
    }

    // Tri décroissant par seeders
    results.sort((a, b) => (b.seeders || 0) - (a.seeders || 0));

    return results;
  }

  async batch(options) {
    return this.single(options);
  }

  async movie(options) {
    return this.single(options);
  }
}
