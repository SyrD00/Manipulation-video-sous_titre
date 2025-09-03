export default {
  id: "nyaa",
  name: "Nyaa.si",
  search: async (query) => {
    const url = `https://nyaa.si/?f=0&c=1_2&q=${encodeURIComponent(query)}`;
    const html = await fetch(url).then(r => r.text());

    const results = [];

    // Regex qui capture : lien magnet, titre, taille, seeders, leechers
    const regex = /<a href="magnet:\?xt=urn:btih:([^"]+)".*?title="([^"]+)".*?<\/tr>/gs;
    let match;

    while ((match = regex.exec(html)) !== null) {
      const row = match[0];

      // Taille (ex: 1.2 GiB)
      const sizeMatch = row.match(/<td class="text-center">([\d.]+\s(?:KiB|MiB|GiB|TiB))<\/td>/);
      const size = sizeMatch ? sizeMatch[1] : "N/A";

      // Seeders / Leechers
      const seedMatch = row.match(/<td class="text-center">(\d+)<\/td>\s*<td class="text-center">(\d+)<\/td>/);
      const seeders = seedMatch ? seedMatch[1] : null;
      const leechers = seedMatch ? seedMatch[2] : null;

      results.push({
        title: match[2],
        magnet: `magnet:?xt=urn:btih:${match[1]}`,
        size,
        seeders,
        leechers,
      });
    }

    return results;
  }
}
