# Guide pages: facts for Ryth to confirm

Updated October 12, 2026. Items are ordered from most to least important.

## Questions only Ryth can answer

- [ ] Photos: none on the site for now (Ryth's choice, October 12). When there
      are some, use your own photos, photos you have written permission to
      use, or free-license photos with their credit line, never photos
      copied from other websites, listings or photographers, and not AI
      images of real places. They go in content/photos.json.
- [ ] Market numbers: on all six area pages since October 12 (Pocono
      Mountains Association of REALTORS® MLS and Greater Lehigh Valley
      REALTORS® MLS, October 2025 to September 2026). The source line names
      PMAR, as Ryth asked. Tannersville's 130 days is a 12-month average;
      Ryth saw a 2026 median CDOM of 115 there, which fits (a few slow sales
      pull an average above the median). Lehigh Valley numbers were
      replaced on October 13 with a documented pull (average DOM, blank DOM
      left out; details in content/mls/lehigh-valley-2026-10.json). The
      earlier Lehigh Valley figures showed 57 and 65 days; the new ones show
      19 and 23, so the first pull counted days differently. Still to
      confirm: how the Pocono (PMAR) days were counted (DOM, CDOM or list to
      closing), and whether either MLS requires its own wording for
      statistics on a website. Refresh the numbers every few months in
      content/market.json.

## From the October 13 review

- [ ] Zillow profile (zillow.com/profile/ryth%20realtor) does not match the
      site: it shows the brokerage as "Coldwell Banker Hearhside- Heather
      Schierloh Group", the office as "1656 Route 209, Brodheasville, PA
      18058". The site, Google and the MLS say Real of Pennsylvania, 1636 US
      209, Suite 106, Brodheadsville, PA 18322. Update Zillow so all match.
- [x] Zillow rating: removed from the homepage, as Ryth asked, so the page
      does not send visitors to Zillow. The Zillow profile stays in the
      site's hidden profile list (config.js, profiles).
- [ ] Zillow profile: add the website address in its settings.
- [x] Google Business Profile: Ryth sent https://share.google/kdEYDmRYLdOX4UNrp,
      now in the site's profile list. If you can, copy the longer address
      from the browser bar after opening it (google.com/maps/…) and swap
      it in; short links can change.
- [x] Broker phone: Ryth confirmed 570.801.7441 is the broker's number.
      The footer keeps it.
- [ ] "149 transactions" and "$49M" are now labeled as HS Group team
      totals on both homepages. Confirm the wording with the broker.
- [x] 9781 Auburn Dr: now $215,000 (was $229,900, per Ryth), with "Price
      reduced $14,900 · was $229,900" on the card. The listings editor has a new optional field,
      "Price before reduction", for the next price cut; clear it to remove
      the line.
- [ ] Monroe County program guide: the only county brochure found is from
      2023, with older amounts, so the guide links the Redevelopment
      Authority's current program page instead.
- [ ] Investing guide sources: the AirDNA figures link to the article on
      PoconoVacationHomeSales.com (another agent's site) where they were
      published. Remove that link if you prefer not to send readers there.

## New pages (October 13, 2026, second group)

Built in English and Spanish:
- Moving to Pennsylvania from New York or New Jersey (taxes compared, commutes, towns, first months)
- Investing in Poconos Real Estate (long-term rentals near the job centers, fix-and-flip, sheriff and tax sales, land)
- Investing in Lehigh Valley Real Estate (MLS rents and 2 to 4 unit prices for Allentown, Bethlehem and Easton)
- Buying a Home in the Lehigh Valley (prices, what each budget buys, city inspections)
- Homepage: Buying in the Lehigh Valley replaced Monroe County among the six cards; the FAQ answers about moving, investing and the Lehigh Valley now link to these pages.

- [ ] Read the four pages and correct anything that does not match how you work.
- [ ] Taxes on the moving page come from the PA Department of Revenue, the NJ Division of Taxation and the Tax Foundation (2026). Have an accountant you trust read that section.
- [ ] Poconos rents: the Poconos investing page has no rent figures yet. Pull median 2- and 3-bedroom rents from the PMAR MLS (Part 2 of the prompt) and I will add them.
- [ ] Ryth's take for each of these pages, in your own words.

## New pages (October 13, 2026, first group)

Built in English and Spanish:
- Buying a Home in the Poconos
- Buying an Airbnb in the Poconos (renamed from the rental investing guide; the old address forwards)
- How to Sell Your House in the Poconos, and in the Lehigh Valley. These replace "How to Sell Your Home in Pennsylvania"; its old address forwards to the Poconos page.
- 8 new questions in the homepage FAQ; Allentown added to the areas served

- [ ] Read the new pages and correct anything that does not match how you work.
- [ ] Out-of-state buyers: tell me how you work with them (video tours? weekend showings?), so the FAQ answer about moving from New York or New Jersey can say it.
- [ ] Ryth's take for each new page, in your own words (2 or 3 sentences).
- [x] Lehigh Valley MLS numbers: received October 13 and added (Allentown, Bethlehem, Easton, Nazareth, Lehigh and Northampton counties). Rents, 2 to 4 unit sales and price ranges are saved in content/mls/ for the Lehigh Valley buying and investing pages.
- [ ] Pocono MLS numbers (Part 2 of the prompt): still needed from the PMAR MLS. The Lehigh Valley MLS's copy of Pocono listings is missing most property types, so it cannot be used. When they arrive, the price tables on the Poconos buying, selling and Airbnb pages fill in on their own (Mount Pocono, Coolbaugh, Tobyhanna Township, Middle Smithfield, Stroud Township).
- [ ] Second-home and investment down payments (10%, 15%, 25%) come from Fannie Mae and Freddie Mac's current tables. Have a lender you trust read that section.

## Spanish site (added October 12, 2026)

- [ ] Read the Spanish pages (es/ and es/guias/). The text is neutral Latin
      American Spanish and uses "usted". Change any word that does not sound
      like you.
- [ ] Your takes are translated into Spanish on the Spanish pages. Check that
      they say what you mean.
- [ ] Testimonials stay in the words the client wrote. If Flor B. (or anyone
      else) first wrote theirs in Spanish, send the original text so the
      Spanish page can show it.
- [ ] Footer in Spanish: "Licencia RS380174 · Bróker: Real of Pennsylvania ·
      Oficina 570.801.7441". Confirm with your broker that Spanish-language
      ads are fine with this wording.

## Settled with Ryth (October 11, 2026)

- Coolbaugh Township is green on the short-term rental map.
- Ryth's takes for Tannersville and Bethlehem are on the pages (Bethlehem's
  reworded without "families", school quality or crime, for fair housing).
- Bethlehem: the seller's resale inspection is no longer in the buyer
  checklist; added the water line map, the city's homebuyer program and the
  homestead exclusion.
- The phone on the Google Business Profile is Ryth's: 929-345-6838.
- Only the license number (RS380174) goes on the site, not the MLS ID or the
  NRDS ID.
- Northampton County page: the map gives each municipality its own color
  (colors only tell neighbors apart).

## Compliance (check with your broker)

- [ ] "In 2025, Ryth and his team at HS Group closed 149 transactions totaling
      $49 million in sales" (author box on every guide, and the homepage bio).
- [ ] Investing guide: "Ryth has closed investment-property deals worth
      millions of dollars", "some of them aiming for six figures a year".
- [ ] Ryth's take on the investing guide: "An average short-term rental home
      here makes between $45,000 and $65,000 a year" (AirDNA figures support
      this range, see below) and "Some homes average more than six figures a
      year".
- [ ] Penn Estates: "several homes there bring in strong income as vacation
      rentals".
- [ ] First-time buyer guide: the buyer-agreement explanation, and the line
      "Some lenders offer mortgages to borrowers with an ITIN."
- [ ] Selling guide: the description of your marketing (photography, social
      media, targeted ads, multiple MLS, AI visualizations).

## Checked against sources (October 2026)

- I-80 enters Pennsylvania from New Jersey on the Delaware Water Gap Toll
  Bridge, in the Monroe County borough of Delaware Water Gap. Northampton
  County's direct roads into New Jersey are I-78 and US 22.
- Lake Naomi Club, 2026 fee sheet: $5,000 application fee, $8,000 initial
  capital contribution, yearly dues $3,980 to $5,970, PPCA assessment $1,058
  per house, Timber Trails assessment $2,890, rental registration $175.
- AirDNA, 12 months to August 2026: Pocono average revenue about $55,200,
  43% occupancy, $397 average nightly rate; East Stroudsburg about $62,300,
  Jim Thorpe about $45,600.
- Pocono Township short-term rental ordinance (Chapter 302, amended 2025):
  Commercial and Recreational districts only, annual license, inspection,
  $500,000 insurance, local contact within 15 miles, 2 per bedroom plus 4 up
  to 14, bedrooms per sewage permit, license not transferable.
- Monroe County hotel room excise tax: 3% (county ordinance 2017-1).
- Monroe County: 79.5% of occupied homes are owner-occupied (US Census
  Bureau, American Community Survey 2019 to 2023).
- City of Bethlehem: resale inspection required before a sale, rules updated
  July 2026; historic district exterior changes go through HARB and City
  Council; rental units licensed yearly and inspected every three years.
- Historic Moravian Bethlehem: UNESCO World Heritage Site since 2024.
- Communities table (investing guide): Indian Mountain Lakes from its 2026
  rental form ($60 per stay, $100 yearly permit, $10 wristbands, gates admit
  only registered guests); Lake Harmony Estates from its own beach page;
  Lake Naomi from the club's 2026 fee sheet. Emerald Lakes, Penn Estates,
  A Pocono Country Place and Stillwater Lake Estates from rental listings
  and agent sites; confirm with each association.
- Bethlehem: the city's Service Line Inventory map (water line material) and
  the Bethlehem Homebuyer Assistance Program (up to 10% down payment plus
  closing costs, 0% loan forgiven over 10 years, income limits apply).
- Village townships, from Census and USGS place data: Tannersville and
  Bartonsville (Pocono), Pocono Pines and Blakeslee (Tobyhanna), Tobyhanna
  village (Coolbaugh), Long Pond (Tunkhannock), Effort (Chestnuthill),
  Kunkletown (Eldred), Cresco and Canadensis (Barrett), Henryville (Paradise),
  Saylorsburg (Hamilton and Ross). Lake Harmony and Albrightsville are in
  Carbon County. Indian Mountain Lakes is in both: Tunkhannock and
  Chestnuthill townships in Monroe, and Penn Forest Township in Carbon.

## From third-party sources (confirm before relying on them)

- The one-line reason for each township's rating, and the community rules in
  the investing guide's table, come from a July 2026 municipal and community
  scorecard published on another Pocono real estate
  agent's website, cross-checked with the
  township ordinances where available. Fees and rules change often.

## Still from general knowledge (all marked "about")

- [ ] Driving times: Stroudsburg to NYC 1.5 to 2 h, Allentown 50 min, Scranton
      45 min; Tannersville to NYC about 85 miles; Pocono Pines to Stroudsburg
      30 min and Scranton 40 min; Bethlehem to NYC about 80 miles and
      Philadelphia about 60 miles; Easton to NYC about 70 miles.
- [ ] School districts: Stroudsburg Area, East Stroudsburg Area, Pocono
      Mountain (Tannersville, Pocono Pines), Bethlehem Area.
- [ ] Commuter buses to New York City run from the Stroudsburg area.
- [ ] Bath: where Route 248 meets Route 512. Blakeslee: where Route 115 meets
      Route 940.
- [ ] Flood-prone creeks named: Brodhead and McMichael (Stroudsburg), Monocacy
      (Bethlehem).
