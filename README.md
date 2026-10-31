# Microsoft 365 plans and features: open dataset

Which Microsoft 365 plans include which features, as a spreadsheet and as JSON, with links to the Microsoft pages behind the values. Free to download, reuse and republish under [CC BY 4.0](LICENSE), with a credit and a link back.

- **Coverage:** 484 features across 25 Microsoft 365 plans and add-on suites, from Business Basic to E7, Frontline and Education. That's one value for every feature and plan, 12,100 in all.
- **Sources:** checked against Microsoft's own documentation: the Product Terms, Microsoft Learn, Microsoft's service plan list, its plan comparison guides and product pages. About half the values (6,392) were researched again from scratch in a separate check.
- **Home page:** https://computecloud.co.uk/data/microsoft-365-plans/. This repository is a copy of the files published there, kept for versioning and archiving on Zenodo.

## Files

| File | What it holds |
|---|---|
| [`data/m365-features.csv`](data/m365-features.csv) | Spreadsheet: one row per feature, one column per plan. Opens in Excel or Google Sheets. |
| [`data/m365-cells.csv`](data/m365-cells.csv) | Every value: one row per feature and plan, with the note and any Microsoft links behind the value. |
| [`data/m365-features.json`](data/m365-features.json) | Full dataset: plans with Microsoft's SKU and service plan IDs, features, values, evidence records and sources. |
| [`data/SHA256SUMS`](data/SHA256SUMS) | Checksums of the three files. |

The JSON's `meta` section holds the version, the counts, the value definitions and a description of every column (`meta.fields`).

## Values

| Value | What it means |
|---|---|
| Included | The plan includes it. |
| Not included | Microsoft's sources show the plan doesn't include it. |
| Add-on | Not included, but an add-on that adds it can be bought for this plan. The add-on is named. |
| Limit | Included with a stated limit or billing model, such as a mailbox size. |
| Partial | Included with a condition, given in the note. |
| Unclear | Microsoft's own documents conflict or don't say clearly. The note explains. |
| Unverified | No Microsoft source either way after a full search. |

The add-on suite columns (the Defender and Purview suites) list only what the suite adds, so a feature already in the base plan shows as not included there. The data doesn't include prices. For those, see [Microsoft 365 pricing in the UK](https://computecloud.co.uk/microsoft-365/pricing/) or the [plan comparison tool](https://computecloud.co.uk/tools/microsoft-365-plans/), which runs on this data.

## How it was built

- **Microsoft's documentation only.** In order of authority:
  1. the Product Terms;
  2. Microsoft Learn licensing pages;
  3. Microsoft's service plan list;
  4. service descriptions;
  5. the plan comparison guides;
  6. Microsoft's product and support pages.

  Resellers, blogs and AI summaries are never a source.
- **What the feature needs, and what the plan carries.** For example, Conditional Access needs Microsoft Entra ID P1. So a plan includes it if its service plans in Microsoft's list carry Entra ID P1, or if Microsoft names the plan.
- **A separate check.** About half the values were researched again from scratch, including every add-on, partial and unclear value. Disagreements were settled against Microsoft's sources.
- **No guessing.** Where Microsoft's own documents disagree, the value is Unclear and the note says why. Where no Microsoft source settles it, the value is Unverified.

The JSON keeps the evidence behind the values: the Microsoft page, the section and the date it was checked.

## How to cite

> ComputeCloud (2026). Microsoft 365 plans and features (version 2026-10-28). https://computecloud.co.uk/data/microsoft-365-plans/. Licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).

For a web page:

```html
Source: <a href="https://computecloud.co.uk/data/microsoft-365-plans/">Microsoft 365 plans and features</a>, ComputeCloud, <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>
```

Each version is also archived on Zenodo with its own DOI. GitHub's "Cite this repository" button uses [`CITATION.cff`](CITATION.cff).

## Licence

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). You can copy, share, adapt and build on the data for any purpose, including commercially, as long as you:

- credit ComputeCloud;
- link to the dataset page and to the licence;
- say if you changed the data.

Microsoft's product names belong to Microsoft, and this dataset is not produced or endorsed by Microsoft.

This is a summary of Microsoft's public documentation on the dates shown, not licensing advice. Microsoft's Product Terms and your own agreement decide what you are licensed for.

**Spotted a mistake?** Tell us at hello@computecloud.co.uk with the feature, the plan and Microsoft's source.

## Versions

Versions are named by date (the first is `2026-10-28`) and listed under [Releases](../../releases) and on the [dataset page](https://computecloud.co.uk/data/microsoft-365-plans/) (under "Changes").

The files here are never edited by hand. Each version happens in this order:

1. ComputeCloud publishes the new version on the website.
2. The **Sync data from the website** workflow copies the three files here and checks they are complete.
3. A release tagged `v<version>` archives that version on Zenodo.
