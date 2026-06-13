# Real-Data Surrogate Calibration: sspec_533f665ec4ac063dbb664a54

This coordinator report is value-free: it records ids, run counts, seeds, gate outcomes, and the declared threshold only. It contains no label, feature, return, diagnostic, signal, or cost values.

## Scope

- Declared K per perturbation config: 3
- Bound statement: zero passes in K bounds false-pass rate at about 3/K at 95%.
- Declared primary horizon used for this run: `5m`.
- Perturbation configs: trade_date_block_shuffle, trade_date_block_bootstrap.
- Runtime factor derivation path: `alpha_system.governance.surrogate_run.study_config_for_surrogate_scope` -> `StudyConfig.from_mapping`.
- Declared feature family: `bbo_tradability_top_book`.
- Declared factor count: 11.
- Declared factors: `bbo_tradability_mid`, `bbo_tradability_spread_zscore`, `bbo_tradability_spread`, `bbo_tradability_spread_ticks`, `bbo_tradability_top_book_depth`, `bbo_tradability_top_book_imbalance`, `bbo_tradability_missing_bbo_flag`, `bbo_tradability_bad_quote_flag`, `bbo_tradability_wide_spread_flag`, `bbo_tradability_low_depth_flag`, `bbo_tradability_microprice`.
- Excluded all-null/constant factor partitions: 74.
- Declared label pack count: 24.
- Declared label versions: `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a`, `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e`, `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64`, `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a`, `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9`, `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022`, `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb`, `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3`, `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b`, `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031`, `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6`, `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2`, `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b`, `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742`, `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57`, `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce`, `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da`, `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515`, `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0`, `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a`, `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b`, `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276`, `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce`, `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b`.
- Staged surrogate sub-config count: 0.
- Off-grid locked label event_ts count: 0.
- Isolated namespace: `/home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_v5_bbo_533f66`.

## Staging Provenance

- No values were staged; `--rescore-existing` mode only rescored outputs.

## excluded_factors

| Factor | Feature Version | Partition | Reason | Rows | Null Rows | Numeric Rows |
|---|---|---|---|---:|---:|---:|
| `bbo_tradability_spread_ticks` | `fver_7eb2c1d84e1b747fc92569ea5305b36f60d3dbcae493ef5adac302eb8bcd405c` | `ES_2019_full_year` | `all_null_values` | 349532 | 349532 | 0 |
| `bbo_tradability_spread_ticks` | `fver_6ac0780897a963a7997fc8b898d6ab8309a49da8c347f12e50ea460647de2f28` | `ES_2020_full_year` | `all_null_values` | 349608 | 349608 | 0 |
| `bbo_tradability_spread_ticks` | `fver_f3c5ce047c95aac0d8bd6deef0451e97ed92b87dfb7ba0337926f8f0805c2b0e` | `ES_2021_full_year` | `all_null_values` | 353363 | 353363 | 0 |
| `bbo_tradability_spread_ticks` | `fver_8ef6d437eaa45fe803dc17247b31cc9d0b81761e78232f38d3cc311a72cd084c` | `ES_2022_full_year` | `all_null_values` | 354119 | 354119 | 0 |
| `bbo_tradability_spread_ticks` | `fver_9e391c824c6827838bce0dc4de23dfa7c1a819366a27330ce8102b9e9ac7f026` | `ES_2023_full_year` | `all_null_values` | 353153 | 353153 | 0 |
| `bbo_tradability_spread_ticks` | `fver_fe6fcc0cd2f91ddadadc1e756ac94129e58fda7e4a9fb8286eaa9e7d970ac284` | `ES_2024_full_year` | `all_null_values` | 346858 | 346858 | 0 |
| `bbo_tradability_spread_ticks` | `fver_1f83ac386a08ce609d691d484c6599b52207d4e877511dadcb230d557557081d` | `ES_2025_full_year` | `all_null_values` | 344561 | 344561 | 0 |
| `bbo_tradability_spread_ticks` | `fver_3a730952000840b0fe4382f746dd001e9f8aacf0f121e37898ea03e12abe0819` | `ES_2026_full_year` | `all_null_values` | 140639 | 140639 | 0 |
| `bbo_tradability_spread_ticks` | `fver_a61510feba9c3fe83aa35b9cfa477564cd6439acdb1c185274e24c0d3e1c00e7` | `NQ_2019_full_year` | `all_null_values` | 349845 | 349845 | 0 |
| `bbo_tradability_spread_ticks` | `fver_56d6fdf2befe66aadda7453762c3f8a6f138cf6a23c447d0c0a89f7c77b7888a` | `NQ_2020_full_year` | `all_null_values` | 348929 | 348929 | 0 |
| `bbo_tradability_spread_ticks` | `fver_c8cb17e23464f2affc4a720d955dfadcc64651790a03dbed43e79647f627bc75` | `NQ_2021_full_year` | `all_null_values` | 353393 | 353393 | 0 |
| `bbo_tradability_spread_ticks` | `fver_5b376810fad4fd715e28f0f70a948fb8a573137bb88fb4850de3a30a334c9ab9` | `NQ_2022_full_year` | `all_null_values` | 354112 | 354112 | 0 |
| `bbo_tradability_spread_ticks` | `fver_510db655d76fad7edc75f44c3712f03043a58c7435fc198615ccd680983e2f3a` | `NQ_2023_full_year` | `all_null_values` | 353358 | 353358 | 0 |
| `bbo_tradability_spread_ticks` | `fver_6ccf67910310b8e4b40e0ee9531107b996b4d0f0056e69b63e164bb056dd1213` | `NQ_2024_full_year` | `all_null_values` | 346992 | 346992 | 0 |
| `bbo_tradability_spread_ticks` | `fver_2eb7fe18dd60153a75bbff69d89cbf38ca2ba41019de84bad63726d31ffb6a1b` | `NQ_2025_full_year` | `all_null_values` | 344529 | 344529 | 0 |
| `bbo_tradability_spread_ticks` | `fver_df2b9a46dc8d12371568cbd1527b68a4a0cb1a8da6229959ef5f02130dd1b55b` | `NQ_2026_full_year` | `all_null_values` | 140610 | 140610 | 0 |
| `bbo_tradability_spread_ticks` | `fver_47be03db2549786eaf855c0cceac0651db37fd1891f16ce5e93dfe3c9e3473f2` | `RTY_2019_full_year` | `all_null_values` | 328841 | 328841 | 0 |
| `bbo_tradability_spread_ticks` | `fver_c9e21b98c145b27b7c9e542a668b7f0ae939f73aba8464be7a6305ea0f251488` | `RTY_2020_full_year` | `all_null_values` | 338085 | 338085 | 0 |
| `bbo_tradability_spread_ticks` | `fver_b8d57caddd2a40f9f47e26ffb4114f0a480833217519e42868ed32c561f6c8dc` | `RTY_2021_full_year` | `all_null_values` | 339895 | 339895 | 0 |
| `bbo_tradability_spread_ticks` | `fver_8bf5b497f2b265b57330ff5c9944d2de80106153c4581b3339e6d58043ffc1bb` | `RTY_2022_full_year` | `all_null_values` | 345162 | 345162 | 0 |
| `bbo_tradability_spread_ticks` | `fver_901fad3c1a462526c649300e5a1d73b399ac07382440b66f6cff95ed70815f46` | `RTY_2023_full_year` | `all_null_values` | 342436 | 342436 | 0 |
| `bbo_tradability_spread_ticks` | `fver_391aed1ecec176fcf1b54b41562dc937b1946067f3b19811225cd48e2149068f` | `RTY_2024_full_year` | `all_null_values` | 333540 | 333540 | 0 |
| `bbo_tradability_spread_ticks` | `fver_cecb9ebb814511b911078772db559252a29299dd71e95dbcf6663502e1e8b5e2` | `RTY_2025_full_year` | `all_null_values` | 333557 | 333557 | 0 |
| `bbo_tradability_spread_ticks` | `fver_dac9d597c14908f870b01fc1b5e66b02a94c918e770e2dc8dff140d8a7c34228` | `RTY_2026_full_year` | `all_null_values` | 138593 | 138593 | 0 |
| `bbo_tradability_missing_bbo_flag` | `fver_78d968a8bb123b26a96c42d66f2ecc16d7f9abb63e0508a520d16ba77640024a` | `ES_2019_full_year` | `constant_factor_zero_variance` | 349532 | 0 | 349532 |
| `bbo_tradability_bad_quote_flag` | `fver_089ee9a7fad5e283764a0d58198115676e9a60096e7b66932f942cf66b7e8dce` | `ES_2019_full_year` | `constant_factor_zero_variance` | 349532 | 0 | 349532 |
| `bbo_tradability_wide_spread_flag` | `fver_ea32b7301c445a7492d48f8fad6e80bd651647340dd8a48d7b5b94ebb668e9fd` | `ES_2019_full_year` | `constant_factor_zero_variance` | 349532 | 3 | 349529 |
| `bbo_tradability_low_depth_flag` | `fver_efec705eb36a859de89d8f196bb7ca8b0e70e90166aeae120e02d0a658cfe88c` | `ES_2019_full_year` | `constant_factor_zero_variance` | 349532 | 3 | 349529 |
| `bbo_tradability_low_depth_flag` | `fver_f75128805419b7961f51d736539f5998a5194309c39607c3aab99ebf24f9e154` | `ES_2020_full_year` | `constant_factor_zero_variance` | 349608 | 494 | 349114 |
| `bbo_tradability_wide_spread_flag` | `fver_50a2d5af38f8bf73ca94dad638c551f5248a41bba0e1833693ea998f07e5217c` | `ES_2021_full_year` | `constant_factor_zero_variance` | 353363 | 1 | 353362 |
| `bbo_tradability_low_depth_flag` | `fver_28bd4156616ed2b13bc201acb7c7f5a7d7da5c12ca367dd2f8479657efbf26f5` | `ES_2021_full_year` | `constant_factor_zero_variance` | 353363 | 1 | 353362 |
| `bbo_tradability_low_depth_flag` | `fver_6977d39b267152eca4096146952594c6032ac6de93c52b590737b9cdded36688` | `ES_2022_full_year` | `constant_factor_zero_variance` | 354119 | 3 | 354116 |
| `bbo_tradability_wide_spread_flag` | `fver_50752a9648d866f2795b638a897ca6a045d425f7e80c1ebef0fb09ad969a1a0f` | `ES_2023_full_year` | `constant_factor_zero_variance` | 353153 | 93 | 353060 |
| `bbo_tradability_low_depth_flag` | `fver_fed6748c9353a53c164f770a23d8ed20f593aac69771c8fa3a17ce6f842b2c34` | `ES_2023_full_year` | `constant_factor_zero_variance` | 353153 | 93 | 353060 |
| `bbo_tradability_wide_spread_flag` | `fver_3a162c4da024b6a81cbf997ba02d47b070bcc13f2f09884a104ee6053f3dc486` | `ES_2024_full_year` | `constant_factor_zero_variance` | 346858 | 1 | 346857 |
| `bbo_tradability_low_depth_flag` | `fver_88d2d46cb7ffc1c9cfff7c5a8cfd3a7553d54ac88360ddc5b869af16394233dd` | `ES_2024_full_year` | `constant_factor_zero_variance` | 346858 | 1 | 346857 |
| `bbo_tradability_wide_spread_flag` | `fver_29da2dcd967071e8eb1b5d6f0618c33a9d80eec7894fcb6da1e9812a39d2cd31` | `ES_2025_full_year` | `constant_factor_zero_variance` | 344561 | 4 | 344557 |
| `bbo_tradability_low_depth_flag` | `fver_2d21e44075a170c4b905bac22ee9a87ff5f14117ae8f1606110151708552b382` | `ES_2025_full_year` | `constant_factor_zero_variance` | 344561 | 4 | 344557 |
| `bbo_tradability_wide_spread_flag` | `fver_0c8ba22ac3bf70b0fed90ceb0787ad992cddd42f881c281bccfcdb9d1537d384` | `ES_2026_full_year` | `constant_factor_zero_variance` | 140639 | 1 | 140638 |
| `bbo_tradability_low_depth_flag` | `fver_b2830836598768a9ef086b090749dcdf1dab441b43360c77427b3fc7ce30ec4d` | `ES_2026_full_year` | `constant_factor_zero_variance` | 140639 | 1 | 140638 |
| `bbo_tradability_wide_spread_flag` | `fver_7d134fa0bd2cbf5fbe008f9af20f11a3cf5ba2e5b4e503d6560afb4f63d01023` | `NQ_2019_full_year` | `constant_factor_zero_variance` | 349845 | 2 | 349843 |
| `bbo_tradability_low_depth_flag` | `fver_1b0f2b023ec92ea4b3d93bb34320648144ac34a5898d359ab79b27ec044a2184` | `NQ_2019_full_year` | `constant_factor_zero_variance` | 349845 | 2 | 349843 |
| `bbo_tradability_low_depth_flag` | `fver_ba9fc407e5ed9cd34bc5898be45de50c5f5cb9e3a23ba95959d456dea2d429f9` | `NQ_2020_full_year` | `constant_factor_zero_variance` | 348929 | 405 | 348524 |
| `bbo_tradability_wide_spread_flag` | `fver_60d8883e7386466ec7108758d072908c72230a26a745907794e88348966cd7f7` | `NQ_2021_full_year` | `constant_factor_zero_variance` | 353393 | 3 | 353390 |
| `bbo_tradability_low_depth_flag` | `fver_3edd1db72636f13ab82552e249f763c260ad2a42151f8181a34063198b23ddfa` | `NQ_2021_full_year` | `constant_factor_zero_variance` | 353393 | 3 | 353390 |
| `bbo_tradability_low_depth_flag` | `fver_3a4c21576455f0cbda894b81a19ec688063160dce27bf273f492f3d42fe600e3` | `NQ_2022_full_year` | `constant_factor_zero_variance` | 354112 | 3 | 354109 |
| `bbo_tradability_wide_spread_flag` | `fver_75cd507bf855180c5c75cdf1f7c7e0a7ee17a563b1e1bf2abfcf98e81aad3863` | `NQ_2023_full_year` | `constant_factor_zero_variance` | 353358 | 92 | 353266 |
| `bbo_tradability_low_depth_flag` | `fver_daa9059ac54b12f561dcb7b1eb81dd2ff7c96f4dbb56c68583d93b9e09c392df` | `NQ_2023_full_year` | `constant_factor_zero_variance` | 353358 | 92 | 353266 |
| `bbo_tradability_wide_spread_flag` | `fver_2380c0a86af332a677944eaff06b41b8279d4064a23794a63b3b1c792ad556a9` | `NQ_2024_full_year` | `constant_factor_zero_variance` | 346992 | 1 | 346991 |
| `bbo_tradability_low_depth_flag` | `fver_e32fdf9814d3e2f365c661c53ba28da9ea4135fcbf9342527d28b1a868354ecc` | `NQ_2024_full_year` | `constant_factor_zero_variance` | 346992 | 1 | 346991 |
| `bbo_tradability_wide_spread_flag` | `fver_cb4b7b04c6c783d9340a4a56a50990c511aab7f3a2ee4ec9f5b026115ee6e810` | `NQ_2025_full_year` | `constant_factor_zero_variance` | 344529 | 10 | 344519 |
| `bbo_tradability_low_depth_flag` | `fver_afe13932f76475c8da55088dd671be26378b3f3107909aa77c05669d7161f59f` | `NQ_2025_full_year` | `constant_factor_zero_variance` | 344529 | 10 | 344519 |
| `bbo_tradability_wide_spread_flag` | `fver_92e6efbbda9633be74f459de126c42d869fd1632512eb0c287037d541e5f89d1` | `NQ_2026_full_year` | `constant_factor_zero_variance` | 140610 | 1 | 140609 |
| `bbo_tradability_low_depth_flag` | `fver_bcc4c7b2774a2c7c8bd31424b0f2d068e8e3f125b3f95e735e8b48af9e0a29f9` | `NQ_2026_full_year` | `constant_factor_zero_variance` | 140610 | 1 | 140609 |
| `bbo_tradability_missing_bbo_flag` | `fver_5360822c9b065a44af5e68eb4445d21fcd433280c7000893e6797e1bcee7d38d` | `RTY_2019_full_year` | `constant_factor_zero_variance` | 328841 | 0 | 328841 |
| `bbo_tradability_bad_quote_flag` | `fver_1feb41b7f2f730123af210950c6e1759971ea97e13def7bd597b9eb983e31b6c` | `RTY_2019_full_year` | `constant_factor_zero_variance` | 328841 | 0 | 328841 |
| `bbo_tradability_wide_spread_flag` | `fver_b759115a857dade2839ab21b95baadaab9624ed6191e8708eff1b2c5572ac20c` | `RTY_2019_full_year` | `constant_factor_zero_variance` | 328841 | 0 | 328841 |
| `bbo_tradability_low_depth_flag` | `fver_42805ade990bfa2a400211bdea850f0e539600a35f9ef6a75ad244897c087eeb` | `RTY_2019_full_year` | `constant_factor_zero_variance` | 328841 | 0 | 328841 |
| `bbo_tradability_low_depth_flag` | `fver_cb6876002a759c0805bb73e2535dfd1d54b6284dd6b5183bc6ff7ade98451b04` | `RTY_2020_full_year` | `constant_factor_zero_variance` | 338085 | 177 | 337908 |
| `bbo_tradability_missing_bbo_flag` | `fver_672744d994715afac374c6bd0c325dcdadcfebee5d29354b2c0cccc87b22b1b5` | `RTY_2021_full_year` | `constant_factor_zero_variance` | 339895 | 0 | 339895 |
| `bbo_tradability_bad_quote_flag` | `fver_86a08c1b72aabbf4b063858705379574857cf777341da47bfd6a47216b2ce301` | `RTY_2021_full_year` | `constant_factor_zero_variance` | 339895 | 0 | 339895 |
| `bbo_tradability_wide_spread_flag` | `fver_e0be973ce508824fbb546842e459a86601f0983559b47cdcbbf3f0843209fada` | `RTY_2021_full_year` | `constant_factor_zero_variance` | 339895 | 0 | 339895 |
| `bbo_tradability_low_depth_flag` | `fver_d4d9ccdbba81240ec38edbd8d8a25ab1d28c3b92d86dc9d8d9a536e70b820e94` | `RTY_2021_full_year` | `constant_factor_zero_variance` | 339895 | 0 | 339895 |
| `bbo_tradability_wide_spread_flag` | `fver_44ebca6626963f0ff55cabed6ce7996a4ccfe9ea122c664636f16e8c26d9bcef` | `RTY_2022_full_year` | `constant_factor_zero_variance` | 345162 | 4 | 345158 |
| `bbo_tradability_low_depth_flag` | `fver_ec7f20504a1202f621242016f8186f7dc9972f31e4ef211faff0f898d7de4f0c` | `RTY_2022_full_year` | `constant_factor_zero_variance` | 345162 | 4 | 345158 |
| `bbo_tradability_wide_spread_flag` | `fver_fcaf7c1d10b8839d2b2a4fd4c6b8b9f2ca25383720b6140284f416dca5cba97e` | `RTY_2023_full_year` | `constant_factor_zero_variance` | 342436 | 41 | 342395 |
| `bbo_tradability_low_depth_flag` | `fver_47193446855b0c58fbf4298bba3e435c9186b1d9fb392e6178c8d1bdf2d770c8` | `RTY_2023_full_year` | `constant_factor_zero_variance` | 342436 | 41 | 342395 |
| `bbo_tradability_missing_bbo_flag` | `fver_15c604fac1031090750739065737e425e723f3a260d5b314a9fda56c7e49f363` | `RTY_2024_full_year` | `constant_factor_zero_variance` | 333540 | 0 | 333540 |
| `bbo_tradability_bad_quote_flag` | `fver_5476ec77f4237284d28e4764c0150100243d2933ce4e8fd166d9f81ad70acba7` | `RTY_2024_full_year` | `constant_factor_zero_variance` | 333540 | 0 | 333540 |
| `bbo_tradability_wide_spread_flag` | `fver_9cb271e01d0a85c376f9a4e2d8f8297d0c6e39a91fcb5b4ee6859a33b78fd0af` | `RTY_2024_full_year` | `constant_factor_zero_variance` | 333540 | 0 | 333540 |
| `bbo_tradability_low_depth_flag` | `fver_dfb1495910d2c5ce5c599dfd34b1e8b5e172978ce73e4cff3060b52dd993e0b1` | `RTY_2024_full_year` | `constant_factor_zero_variance` | 333540 | 0 | 333540 |
| `bbo_tradability_low_depth_flag` | `fver_5c93f4f462f8df3d4f46872f99fb2cef1df86c997359023971c803b5afeddcb7` | `RTY_2025_full_year` | `constant_factor_zero_variance` | 333557 | 4 | 333553 |
| `bbo_tradability_wide_spread_flag` | `fver_e248f89aeb375081ec815cf232fcb012dde0396d08a1b1f845c45d61758609a0` | `RTY_2026_full_year` | `constant_factor_zero_variance` | 138593 | 1 | 138592 |
| `bbo_tradability_low_depth_flag` | `fver_93523a56c059fc982507052d5a7633fb5b7e20816876ae5b6296c73ff651b0f1` | `RTY_2026_full_year` | `constant_factor_zero_variance` | 138593 | 1 | 138592 |

This report is value-free: it records run counts, seeds, gate outcomes, and the declared threshold only. It contains no label, feature, return, or diagnostic values.

## Threshold

- Declared threshold: zero shuffled runs may clear the shared detection statistic.
- Statistic: `directional.pearson_ic` absolute value against threshold `0.950000`.
- Threshold verdict: `zero-pass-met`.
- Any shuffled statistic pass is `LEAKAGE_BLOCKED` and requires diagnosis before the kill-shot resumes.
- `eligibility_clean` records warning-free diagnostics as context only; it is not the pass criterion.
- Errored runs block calibration success and are not counted as non-passes.
- Bound statement: zero passes in K bounds false-pass rate at about 3/K at 95%.

## Synthetic Calibration Summary

- Run count: 1140
- Error count: 0
- Statistic pass count: 0
- Statistic pass rate: 0.000000
- Eligibility clean count: 1092

## Per-Perturbation Counts

| Perturbation | Runs | Errors | Statistic Passes | Eligibility Clean | Statistic Pass Rate | Verdict |
|---|---:|---:|---:|---:|---:|---|
| trade_date_block_bootstrap | 570 | 0 | 0 | 546 | 0.000000 | zero-pass-met |
| trade_date_block_shuffle | 570 | 0 | 0 | 546 | 0.000000 | zero-pass-met |

## Per-Run Seeds And Outcomes

| StudySpec | Perturbation | Seed | Outcome | Statistic Passed | Eligibility Clean | Surrogate ID | Reason |
|---|---|---:|---|---|---|---|---|
| sspec_4fa746784450d2c524017fa4 | trade_date_block_shuffle | 10500 | BLOCKED | False | True | surrun_9b65b54db8acdd6fe692ea0f | UNDERPOWERED |
| sspec_4fa746784450d2c524017fa4 | trade_date_block_shuffle | 10501 | BLOCKED | False | True | surrun_f42434a59da62e2c29a9400f | UNDERPOWERED |
| sspec_4fa746784450d2c524017fa4 | trade_date_block_shuffle | 10502 | BLOCKED | False | True | surrun_5ccdd253ad3de2edb1b09017 | UNDERPOWERED |
| sspec_1c57243ef0c7c60974874414 | trade_date_block_shuffle | 10503 | BLOCKED | False | False | surrun_20f2ce885da39f4fa6e23617 | UNDERPOWERED |
| sspec_1c57243ef0c7c60974874414 | trade_date_block_shuffle | 10504 | BLOCKED | False | False | surrun_9d9e498abbaf7dba9112c247 | UNDERPOWERED |
| sspec_1c57243ef0c7c60974874414 | trade_date_block_shuffle | 10505 | BLOCKED | False | False | surrun_fa1f1b0d8e46618080df5511 | UNDERPOWERED |
| sspec_319a2690890476bc88427bf4 | trade_date_block_shuffle | 10506 | BLOCKED | False | True | surrun_c1d9a4eede8b72bb365e3830 | UNDERPOWERED |
| sspec_319a2690890476bc88427bf4 | trade_date_block_shuffle | 10507 | BLOCKED | False | True | surrun_75a219ff6fbd50e5a5c06110 | UNDERPOWERED |
| sspec_319a2690890476bc88427bf4 | trade_date_block_shuffle | 10508 | BLOCKED | False | True | surrun_c0e457a7dcf9f3101b2f6624 | UNDERPOWERED |
| sspec_5c5c2c5889d9efe89bd8b5ef | trade_date_block_shuffle | 10509 | BLOCKED | False | True | surrun_62a17dc54fb4916ab3a78638 | UNDERPOWERED |
| sspec_5c5c2c5889d9efe89bd8b5ef | trade_date_block_shuffle | 10510 | BLOCKED | False | True | surrun_775339a9eda0c861df34e212 | UNDERPOWERED |
| sspec_5c5c2c5889d9efe89bd8b5ef | trade_date_block_shuffle | 10511 | BLOCKED | False | True | surrun_889f6e2f4cc48072c12de689 | UNDERPOWERED |
| sspec_ea87025ac137123d3fdb2c93 | trade_date_block_shuffle | 10512 | BLOCKED | False | True | surrun_8cb406d4097f000348267f70 | UNDERPOWERED |
| sspec_ea87025ac137123d3fdb2c93 | trade_date_block_shuffle | 10513 | BLOCKED | False | True | surrun_67e1cbb3fea4b7190c33836c | UNDERPOWERED |
| sspec_ea87025ac137123d3fdb2c93 | trade_date_block_shuffle | 10514 | BLOCKED | False | True | surrun_269b630778e4a7dff1d2971c | UNDERPOWERED |
| sspec_00839ae5b9943f831d39227b | trade_date_block_shuffle | 10527 | BLOCKED | False | True | surrun_2b74bc2966c91731f132d470 | UNDERPOWERED |
| sspec_00839ae5b9943f831d39227b | trade_date_block_shuffle | 10528 | BLOCKED | False | True | surrun_15944a4d9629a491638c782f | UNDERPOWERED |
| sspec_00839ae5b9943f831d39227b | trade_date_block_shuffle | 10529 | BLOCKED | False | True | surrun_0d70c784699b8e7ab0157970 | UNDERPOWERED |
| sspec_e564d69e4a8ef7e527b12504 | trade_date_block_shuffle | 10530 | BLOCKED | False | True | surrun_d162c9541750d86d382ec071 | UNDERPOWERED |
| sspec_e564d69e4a8ef7e527b12504 | trade_date_block_shuffle | 10531 | BLOCKED | False | True | surrun_d3fd7974dbac9bd27ac5d3ee | UNDERPOWERED |
| sspec_e564d69e4a8ef7e527b12504 | trade_date_block_shuffle | 10532 | BLOCKED | False | True | surrun_373e075fc7b429111799e563 | UNDERPOWERED |
| sspec_acb32ca61cf5a0db09f9de1e | trade_date_block_shuffle | 10533 | BLOCKED | False | False | surrun_8b5108a023824c630dfd06e7 | UNDERPOWERED |
| sspec_acb32ca61cf5a0db09f9de1e | trade_date_block_shuffle | 10534 | BLOCKED | False | False | surrun_87fe6e74492407218925c426 | UNDERPOWERED |
| sspec_acb32ca61cf5a0db09f9de1e | trade_date_block_shuffle | 10535 | BLOCKED | False | False | surrun_99d0481392c38ae606ea6272 | UNDERPOWERED |
| sspec_944e13f0744afe9fdd238171 | trade_date_block_shuffle | 10536 | BLOCKED | False | True | surrun_6be9087448fdbe850994c28b | UNDERPOWERED |
| sspec_944e13f0744afe9fdd238171 | trade_date_block_shuffle | 10537 | BLOCKED | False | True | surrun_2c3f32a8ba2d62ec8fb65a10 | UNDERPOWERED |
| sspec_944e13f0744afe9fdd238171 | trade_date_block_shuffle | 10538 | BLOCKED | False | True | surrun_e175bc35da73275719bfd76c | UNDERPOWERED |
| sspec_89dd5997cfe81a14b68e1f7c | trade_date_block_shuffle | 10539 | BLOCKED | False | True | surrun_3807f9d9b0a0df237f85c954 | UNDERPOWERED |
| sspec_89dd5997cfe81a14b68e1f7c | trade_date_block_shuffle | 10540 | BLOCKED | False | True | surrun_32e1104149905f54ccf17f44 | UNDERPOWERED |
| sspec_89dd5997cfe81a14b68e1f7c | trade_date_block_shuffle | 10541 | BLOCKED | False | True | surrun_aca653ec446e9cb4263a3dd4 | UNDERPOWERED |
| sspec_36204b43ca6b58dbb7701c08 | trade_date_block_shuffle | 10542 | BLOCKED | False | True | surrun_0eae64e427afefef9df67d6c | UNDERPOWERED |
| sspec_36204b43ca6b58dbb7701c08 | trade_date_block_shuffle | 10543 | BLOCKED | False | True | surrun_e441c789755ee685ab509742 | UNDERPOWERED |
| sspec_36204b43ca6b58dbb7701c08 | trade_date_block_shuffle | 10544 | BLOCKED | False | True | surrun_98a0ec4fd2c87654c22c0254 | UNDERPOWERED |
| sspec_36a36f0485335d18313d8e0e | trade_date_block_shuffle | 10545 | BLOCKED | False | True | surrun_c072d88acf4de12009255bbc | UNDERPOWERED |
| sspec_36a36f0485335d18313d8e0e | trade_date_block_shuffle | 10546 | BLOCKED | False | True | surrun_3a6f01148ecc0175b7aa7fb7 | UNDERPOWERED |
| sspec_36a36f0485335d18313d8e0e | trade_date_block_shuffle | 10547 | BLOCKED | False | True | surrun_6b40b2d5c0b6d84bfb1221ae | UNDERPOWERED |
| sspec_0ebc6d34934a8aedee7471a8 | trade_date_block_shuffle | 10548 | BLOCKED | False | True | surrun_37c0886157afa62ba922dcb2 | UNDERPOWERED |
| sspec_0ebc6d34934a8aedee7471a8 | trade_date_block_shuffle | 10549 | BLOCKED | False | True | surrun_321fd64894dd1b9eaf8028c2 | UNDERPOWERED |
| sspec_0ebc6d34934a8aedee7471a8 | trade_date_block_shuffle | 10550 | BLOCKED | False | True | surrun_db78073a2daf8a419ab647f8 | UNDERPOWERED |
| sspec_55eb525b1eee4eff7cac1bdf | trade_date_block_shuffle | 10551 | BLOCKED | False | True | surrun_4f0126cbf7cb152a3865eb07 | UNDERPOWERED |
| sspec_55eb525b1eee4eff7cac1bdf | trade_date_block_shuffle | 10552 | BLOCKED | False | True | surrun_b8e9eab9646c5fb5d337ea7b | UNDERPOWERED |
| sspec_55eb525b1eee4eff7cac1bdf | trade_date_block_shuffle | 10553 | BLOCKED | False | True | surrun_29af28b332ef9cd8adab3819 | UNDERPOWERED |
| sspec_72b4c4fa564ff882a84d22ca | trade_date_block_shuffle | 10557 | BLOCKED | False | True | surrun_7264ce998a7098b8503037f1 | UNDERPOWERED |
| sspec_72b4c4fa564ff882a84d22ca | trade_date_block_shuffle | 10558 | BLOCKED | False | True | surrun_f315ebdf2e2aa1737ce2809b | UNDERPOWERED |
| sspec_72b4c4fa564ff882a84d22ca | trade_date_block_shuffle | 10559 | BLOCKED | False | True | surrun_f1e4ed4255fafa9fcaf65382 | UNDERPOWERED |
| sspec_a39a5a070a5625740fae6601 | trade_date_block_shuffle | 10560 | BLOCKED | False | True | surrun_0707abcc730c7d0103c47af0 | UNDERPOWERED |
| sspec_a39a5a070a5625740fae6601 | trade_date_block_shuffle | 10561 | BLOCKED | False | True | surrun_4615052d6cea4bfa34aa7205 | UNDERPOWERED |
| sspec_a39a5a070a5625740fae6601 | trade_date_block_shuffle | 10562 | BLOCKED | False | True | surrun_1ed765d093957edaa173704f | UNDERPOWERED |
| sspec_3ddbe3eced9b9facefc9d426 | trade_date_block_shuffle | 10563 | BLOCKED | False | False | surrun_7f440fe84fa03863eb914500 | UNDERPOWERED |
| sspec_3ddbe3eced9b9facefc9d426 | trade_date_block_shuffle | 10564 | BLOCKED | False | False | surrun_7fb106da59a429d42ba9667a | UNDERPOWERED |
| sspec_3ddbe3eced9b9facefc9d426 | trade_date_block_shuffle | 10565 | BLOCKED | False | False | surrun_a3f85bbf35174134236d3d81 | UNDERPOWERED |
| sspec_173b965245816178171ff8ef | trade_date_block_shuffle | 10566 | BLOCKED | False | True | surrun_09976ce4b00b60003b37a5bd | UNDERPOWERED |
| sspec_173b965245816178171ff8ef | trade_date_block_shuffle | 10567 | BLOCKED | False | True | surrun_eeb63391c9af37c021664c3c | UNDERPOWERED |
| sspec_173b965245816178171ff8ef | trade_date_block_shuffle | 10568 | BLOCKED | False | True | surrun_a51fe6b7c84871951bfc9fa1 | UNDERPOWERED |
| sspec_b00754db8caafd5990665ab9 | trade_date_block_shuffle | 10569 | BLOCKED | False | True | surrun_9ffb9975d5eeebd1794b68a6 | UNDERPOWERED |
| sspec_b00754db8caafd5990665ab9 | trade_date_block_shuffle | 10570 | BLOCKED | False | True | surrun_0ae17b17978d4b6670618c44 | UNDERPOWERED |
| sspec_b00754db8caafd5990665ab9 | trade_date_block_shuffle | 10571 | BLOCKED | False | True | surrun_b6a2874938b3f4d3b84d1eb4 | UNDERPOWERED |
| sspec_77f49aefe2063edf9fcd9fe6 | trade_date_block_shuffle | 10572 | BLOCKED | False | True | surrun_2a1a4e1d846a36242add7e07 | UNDERPOWERED |
| sspec_77f49aefe2063edf9fcd9fe6 | trade_date_block_shuffle | 10573 | BLOCKED | False | True | surrun_fb10850ea40365ee80070d27 | UNDERPOWERED |
| sspec_77f49aefe2063edf9fcd9fe6 | trade_date_block_shuffle | 10574 | BLOCKED | False | True | surrun_053f447536a5f8df0296e5cb | UNDERPOWERED |
| sspec_a6516a8847202e7da75ad5cb | trade_date_block_shuffle | 10575 | BLOCKED | False | True | surrun_85bf2d5ba5445a8bba767616 | UNDERPOWERED |
| sspec_a6516a8847202e7da75ad5cb | trade_date_block_shuffle | 10576 | BLOCKED | False | True | surrun_c7224d6d62a11c219c0bd1f6 | UNDERPOWERED |
| sspec_a6516a8847202e7da75ad5cb | trade_date_block_shuffle | 10577 | BLOCKED | False | True | surrun_4a5e466aa258b8a332c76e26 | UNDERPOWERED |
| sspec_c5e1b38c31b506856a875ef3 | trade_date_block_shuffle | 10578 | BLOCKED | False | True | surrun_b90912ee7cd9e1c87d36dc23 | UNDERPOWERED |
| sspec_c5e1b38c31b506856a875ef3 | trade_date_block_shuffle | 10579 | BLOCKED | False | True | surrun_4f3182eed96b889e1de2e316 | UNDERPOWERED |
| sspec_c5e1b38c31b506856a875ef3 | trade_date_block_shuffle | 10580 | BLOCKED | False | True | surrun_3a94e1732d16d115d8e9b353 | UNDERPOWERED |
| sspec_573fbf60517c40db277e1f0f | trade_date_block_shuffle | 10587 | BLOCKED | False | True | surrun_d7da767d4020b6a554864fea | UNDERPOWERED |
| sspec_573fbf60517c40db277e1f0f | trade_date_block_shuffle | 10588 | BLOCKED | False | True | surrun_50ad7e5f60f8af85079e183b | UNDERPOWERED |
| sspec_573fbf60517c40db277e1f0f | trade_date_block_shuffle | 10589 | BLOCKED | False | True | surrun_d0f287759144a868141f12b9 | UNDERPOWERED |
| sspec_0da1b86bd637df69b484dc17 | trade_date_block_shuffle | 10590 | BLOCKED | False | True | surrun_5e9c036ce99d42e204d60f05 | UNDERPOWERED |
| sspec_0da1b86bd637df69b484dc17 | trade_date_block_shuffle | 10591 | BLOCKED | False | True | surrun_e9c509bfb55307c72d5cb2d1 | UNDERPOWERED |
| sspec_0da1b86bd637df69b484dc17 | trade_date_block_shuffle | 10592 | BLOCKED | False | True | surrun_7feff117918240b4455502ab | UNDERPOWERED |
| sspec_ac9de244fbb515f2fa22615d | trade_date_block_shuffle | 10593 | BLOCKED | False | False | surrun_1d7c01cd7b21c7251067f376 | UNDERPOWERED |
| sspec_ac9de244fbb515f2fa22615d | trade_date_block_shuffle | 10594 | BLOCKED | False | False | surrun_ff23243a2133f12eeba79f99 | UNDERPOWERED |
| sspec_ac9de244fbb515f2fa22615d | trade_date_block_shuffle | 10595 | BLOCKED | False | False | surrun_a8f0ec177bae94b00c52069d | UNDERPOWERED |
| sspec_3f391da448f5d99814a7e9db | trade_date_block_shuffle | 10596 | BLOCKED | False | True | surrun_a7b3a74b3cd253ec36f48d03 | UNDERPOWERED |
| sspec_3f391da448f5d99814a7e9db | trade_date_block_shuffle | 10597 | BLOCKED | False | True | surrun_3d6fd8d57c86a0f6b52a95ed | UNDERPOWERED |
| sspec_3f391da448f5d99814a7e9db | trade_date_block_shuffle | 10598 | BLOCKED | False | True | surrun_d47d35d40a93595006e99e28 | UNDERPOWERED |
| sspec_b9385c7ac215e605906f6d6e | trade_date_block_shuffle | 10599 | BLOCKED | False | True | surrun_cad6b29c1ac30822ebc3e4e4 | UNDERPOWERED |
| sspec_b9385c7ac215e605906f6d6e | trade_date_block_shuffle | 10600 | BLOCKED | False | True | surrun_abf76664a49fcd03f97d232d | UNDERPOWERED |
| sspec_b9385c7ac215e605906f6d6e | trade_date_block_shuffle | 10601 | BLOCKED | False | True | surrun_f0ec45cdccd4a8e0d24fba71 | UNDERPOWERED |
| sspec_470f031a3b85a887bad9f587 | trade_date_block_shuffle | 10602 | BLOCKED | False | True | surrun_5ba7b5ee11e7107c9a5f6709 | UNDERPOWERED |
| sspec_470f031a3b85a887bad9f587 | trade_date_block_shuffle | 10603 | BLOCKED | False | True | surrun_8f02949b382cf29828b90146 | UNDERPOWERED |
| sspec_470f031a3b85a887bad9f587 | trade_date_block_shuffle | 10604 | BLOCKED | False | True | surrun_c8b5f961db62dddb3e059efa | UNDERPOWERED |
| sspec_52095f4e99ebe557b96d4639 | trade_date_block_shuffle | 10605 | BLOCKED | False | True | surrun_0b96df6bf9cc7fd19e49f7fc | UNDERPOWERED |
| sspec_52095f4e99ebe557b96d4639 | trade_date_block_shuffle | 10606 | BLOCKED | False | True | surrun_c75a246cde88d063df58bfba | UNDERPOWERED |
| sspec_52095f4e99ebe557b96d4639 | trade_date_block_shuffle | 10607 | BLOCKED | False | True | surrun_7bec038ab7f93d721c01adef | UNDERPOWERED |
| sspec_40eddd44e9e5dee029c1d699 | trade_date_block_shuffle | 10608 | BLOCKED | False | True | surrun_b12477a8453e61fc37e13acb | UNDERPOWERED |
| sspec_40eddd44e9e5dee029c1d699 | trade_date_block_shuffle | 10609 | BLOCKED | False | True | surrun_23fb45c69b4de180be608252 | UNDERPOWERED |
| sspec_40eddd44e9e5dee029c1d699 | trade_date_block_shuffle | 10610 | BLOCKED | False | True | surrun_4a7967f2d9e5caf497f49a37 | UNDERPOWERED |
| sspec_af34dfb90556059712d9deb2 | trade_date_block_shuffle | 10611 | BLOCKED | False | True | surrun_0cdd6bcf304813285283dfab | UNDERPOWERED |
| sspec_af34dfb90556059712d9deb2 | trade_date_block_shuffle | 10612 | BLOCKED | False | True | surrun_443b908f34644a0f50bc21b4 | UNDERPOWERED |
| sspec_af34dfb90556059712d9deb2 | trade_date_block_shuffle | 10613 | BLOCKED | False | True | surrun_2249ad6edbb06c7994d45051 | UNDERPOWERED |
| sspec_6cbd4448bb637b57a5798941 | trade_date_block_shuffle | 10617 | BLOCKED | False | True | surrun_8fb44b81b770ce1089bf467b | UNDERPOWERED |
| sspec_6cbd4448bb637b57a5798941 | trade_date_block_shuffle | 10618 | BLOCKED | False | True | surrun_1998dca5d9e3123f83095786 | UNDERPOWERED |
| sspec_6cbd4448bb637b57a5798941 | trade_date_block_shuffle | 10619 | BLOCKED | False | True | surrun_8fae76128f66fb6f33bf35b8 | UNDERPOWERED |
| sspec_9db4771cbb0bfd2e1dc16587 | trade_date_block_shuffle | 10620 | BLOCKED | False | True | surrun_253f7557cd6b14fb290f2c5f | UNDERPOWERED |
| sspec_9db4771cbb0bfd2e1dc16587 | trade_date_block_shuffle | 10621 | BLOCKED | False | True | surrun_c2016e0fe32c37713c559dfe | UNDERPOWERED |
| sspec_9db4771cbb0bfd2e1dc16587 | trade_date_block_shuffle | 10622 | BLOCKED | False | True | surrun_41c27c21165b435caf43f4bd | UNDERPOWERED |
| sspec_05b3a4d953a49c77aa1cc5eb | trade_date_block_shuffle | 10623 | BLOCKED | False | False | surrun_c1b4b6c90118ba2961750d2e | UNDERPOWERED |
| sspec_05b3a4d953a49c77aa1cc5eb | trade_date_block_shuffle | 10624 | BLOCKED | False | False | surrun_abb80543e4352d00000a325c | UNDERPOWERED |
| sspec_05b3a4d953a49c77aa1cc5eb | trade_date_block_shuffle | 10625 | BLOCKED | False | False | surrun_b8213d7463b329d3ec629ff0 | UNDERPOWERED |
| sspec_a44f6ffdeb0ef3d9fe989c74 | trade_date_block_shuffle | 10626 | BLOCKED | False | True | surrun_52326790bf205772d27fb2e5 | UNDERPOWERED |
| sspec_a44f6ffdeb0ef3d9fe989c74 | trade_date_block_shuffle | 10627 | BLOCKED | False | True | surrun_fb1e68765b169a74cc330e6b | UNDERPOWERED |
| sspec_a44f6ffdeb0ef3d9fe989c74 | trade_date_block_shuffle | 10628 | BLOCKED | False | True | surrun_1b52c0cf9bc818f3021abdc3 | UNDERPOWERED |
| sspec_73a87c9e9bb8f8abbf71489d | trade_date_block_shuffle | 10629 | BLOCKED | False | True | surrun_aa3f5032e247e3ccd65222ff | UNDERPOWERED |
| sspec_73a87c9e9bb8f8abbf71489d | trade_date_block_shuffle | 10630 | BLOCKED | False | True | surrun_14355d192c696ace1e473d77 | UNDERPOWERED |
| sspec_73a87c9e9bb8f8abbf71489d | trade_date_block_shuffle | 10631 | BLOCKED | False | True | surrun_2b947b56684c25b7322b2461 | UNDERPOWERED |
| sspec_2f878cd3fc2024e7ea421e27 | trade_date_block_shuffle | 10632 | BLOCKED | False | True | surrun_00c7e12f579899eae4a47efb | UNDERPOWERED |
| sspec_2f878cd3fc2024e7ea421e27 | trade_date_block_shuffle | 10633 | BLOCKED | False | True | surrun_a7d6d49970d433065db1a9e1 | UNDERPOWERED |
| sspec_2f878cd3fc2024e7ea421e27 | trade_date_block_shuffle | 10634 | BLOCKED | False | True | surrun_7d81f4dfa01d0ee86a1aafcf | UNDERPOWERED |
| sspec_1f17dbacaeea51d6adc19b62 | trade_date_block_shuffle | 10635 | BLOCKED | False | True | surrun_a556c7c1a3f4ad146c6b2883 | UNDERPOWERED |
| sspec_1f17dbacaeea51d6adc19b62 | trade_date_block_shuffle | 10636 | BLOCKED | False | True | surrun_017db991d2fe116b316bf5c2 | UNDERPOWERED |
| sspec_1f17dbacaeea51d6adc19b62 | trade_date_block_shuffle | 10637 | BLOCKED | False | True | surrun_047c6d97ff83fb3aaf0df3a2 | UNDERPOWERED |
| sspec_42b7484aa7400a013c35979e | trade_date_block_shuffle | 10638 | BLOCKED | False | True | surrun_6f9987b679d74bd5c17a1093 | UNDERPOWERED |
| sspec_42b7484aa7400a013c35979e | trade_date_block_shuffle | 10639 | BLOCKED | False | True | surrun_0fa77dd65cf7f60b3404c200 | UNDERPOWERED |
| sspec_42b7484aa7400a013c35979e | trade_date_block_shuffle | 10640 | BLOCKED | False | True | surrun_b20d051ba15caf51cbbdb337 | UNDERPOWERED |
| sspec_83973637948a060c1a01d3ec | trade_date_block_shuffle | 10647 | BLOCKED | False | True | surrun_58504a4be1a50f45eadac52d | UNDERPOWERED |
| sspec_83973637948a060c1a01d3ec | trade_date_block_shuffle | 10648 | BLOCKED | False | True | surrun_d54f633b00afaf2449fee288 | UNDERPOWERED |
| sspec_83973637948a060c1a01d3ec | trade_date_block_shuffle | 10649 | BLOCKED | False | True | surrun_023db6e7cd5454421a2d9b39 | UNDERPOWERED |
| sspec_6182442ead006ecd05c0bfc6 | trade_date_block_shuffle | 10650 | BLOCKED | False | True | surrun_fb3ef3c0b084deee8e3226ba | UNDERPOWERED |
| sspec_6182442ead006ecd05c0bfc6 | trade_date_block_shuffle | 10651 | BLOCKED | False | True | surrun_f6459b1c08b59d910df3c1e6 | UNDERPOWERED |
| sspec_6182442ead006ecd05c0bfc6 | trade_date_block_shuffle | 10652 | BLOCKED | False | True | surrun_fa9c00cf805273c74699b982 | UNDERPOWERED |
| sspec_af22bf758cac2e63e4dc15c0 | trade_date_block_shuffle | 10653 | BLOCKED | False | False | surrun_1dfc95fe74bd28e4e19fc8f9 | UNDERPOWERED |
| sspec_af22bf758cac2e63e4dc15c0 | trade_date_block_shuffle | 10654 | BLOCKED | False | False | surrun_2624435c9747ba8fb99d36da | UNDERPOWERED |
| sspec_af22bf758cac2e63e4dc15c0 | trade_date_block_shuffle | 10655 | BLOCKED | False | False | surrun_84e86a5a631479d006969801 | UNDERPOWERED |
| sspec_bacc76cfa935c22e95cff9c2 | trade_date_block_shuffle | 10656 | BLOCKED | False | True | surrun_171a9b046c687b36bdba08e0 | UNDERPOWERED |
| sspec_bacc76cfa935c22e95cff9c2 | trade_date_block_shuffle | 10657 | BLOCKED | False | True | surrun_98da47623d2f95fb28c41730 | UNDERPOWERED |
| sspec_bacc76cfa935c22e95cff9c2 | trade_date_block_shuffle | 10658 | BLOCKED | False | True | surrun_32b811de27e4d6ea4632e3f3 | UNDERPOWERED |
| sspec_2f7befddef61d91d4f89fd55 | trade_date_block_shuffle | 10659 | BLOCKED | False | True | surrun_6b5817413733a171cfc1b85c | UNDERPOWERED |
| sspec_2f7befddef61d91d4f89fd55 | trade_date_block_shuffle | 10660 | BLOCKED | False | True | surrun_f565af60f108a8cf66a7855f | UNDERPOWERED |
| sspec_2f7befddef61d91d4f89fd55 | trade_date_block_shuffle | 10661 | BLOCKED | False | True | surrun_2bd2a132254f24b200313429 | UNDERPOWERED |
| sspec_01f0aa8d473da54027cde20c | trade_date_block_shuffle | 10662 | BLOCKED | False | True | surrun_f836cb4e535cd962f7995dce | UNDERPOWERED |
| sspec_01f0aa8d473da54027cde20c | trade_date_block_shuffle | 10663 | BLOCKED | False | True | surrun_30b74275d58f2b7f806889cf | UNDERPOWERED |
| sspec_01f0aa8d473da54027cde20c | trade_date_block_shuffle | 10664 | BLOCKED | False | True | surrun_e232f595c6c492f29c97da86 | UNDERPOWERED |
| sspec_67ab4b458039125b4bdce718 | trade_date_block_shuffle | 10665 | BLOCKED | False | True | surrun_d0319f1e6c81767ef9abdc64 | UNDERPOWERED |
| sspec_67ab4b458039125b4bdce718 | trade_date_block_shuffle | 10666 | BLOCKED | False | True | surrun_b12f969dc1a63759d72e1258 | UNDERPOWERED |
| sspec_67ab4b458039125b4bdce718 | trade_date_block_shuffle | 10667 | BLOCKED | False | True | surrun_7a7bae665b39150c66184c9e | UNDERPOWERED |
| sspec_a14c646b8b4c76bcafbfc9eb | trade_date_block_shuffle | 10668 | BLOCKED | False | True | surrun_5a0bbe8e8f6c84091077d20d | UNDERPOWERED |
| sspec_a14c646b8b4c76bcafbfc9eb | trade_date_block_shuffle | 10669 | BLOCKED | False | True | surrun_aab95cc605c26ad0537f5298 | UNDERPOWERED |
| sspec_a14c646b8b4c76bcafbfc9eb | trade_date_block_shuffle | 10670 | BLOCKED | False | True | surrun_7aa3cb7ddcd9db3f8ec2aa1c | UNDERPOWERED |
| sspec_89d14d5cbf1c84899310e61f | trade_date_block_shuffle | 10677 | BLOCKED | False | True | surrun_c315fa72e853c66088e8f725 | UNDERPOWERED |
| sspec_89d14d5cbf1c84899310e61f | trade_date_block_shuffle | 10678 | BLOCKED | False | True | surrun_14dcdcffc0b16ca89b5c36e6 | UNDERPOWERED |
| sspec_89d14d5cbf1c84899310e61f | trade_date_block_shuffle | 10679 | BLOCKED | False | True | surrun_bcaa95ad949e2e007aa102f1 | UNDERPOWERED |
| sspec_9b066dbd9d80291f1ff74b27 | trade_date_block_shuffle | 10680 | BLOCKED | False | True | surrun_af9a518a3ebdf789366248f0 | UNDERPOWERED |
| sspec_9b066dbd9d80291f1ff74b27 | trade_date_block_shuffle | 10681 | BLOCKED | False | True | surrun_ee86ee71a2dd4dfbd817f91a | UNDERPOWERED |
| sspec_9b066dbd9d80291f1ff74b27 | trade_date_block_shuffle | 10682 | BLOCKED | False | True | surrun_ff056b19084e0dc1009edecb | UNDERPOWERED |
| sspec_b88f6a5a7a8dc7236e664b7e | trade_date_block_shuffle | 10683 | BLOCKED | False | False | surrun_26a3716d2d6f8e6e0238c360 | UNDERPOWERED |
| sspec_b88f6a5a7a8dc7236e664b7e | trade_date_block_shuffle | 10684 | BLOCKED | False | False | surrun_6fc4f832d7f5fbb7f1a4bf9d | UNDERPOWERED |
| sspec_b88f6a5a7a8dc7236e664b7e | trade_date_block_shuffle | 10685 | BLOCKED | False | False | surrun_e24588ad4b1a490c0aba419e | UNDERPOWERED |
| sspec_be3a8ed3aefcb6e180f8835b | trade_date_block_shuffle | 10686 | BLOCKED | False | True | surrun_0d30ef65ba819a9a0c000c7d | UNDERPOWERED |
| sspec_be3a8ed3aefcb6e180f8835b | trade_date_block_shuffle | 10687 | BLOCKED | False | True | surrun_d45942577092424b6def6279 | UNDERPOWERED |
| sspec_be3a8ed3aefcb6e180f8835b | trade_date_block_shuffle | 10688 | BLOCKED | False | True | surrun_ee389cc9e67ed869cd4ce160 | UNDERPOWERED |
| sspec_dfa123db9ed79da51e68e86a | trade_date_block_shuffle | 10689 | BLOCKED | False | True | surrun_2e7c83f9dfde7076ded096a4 | UNDERPOWERED |
| sspec_dfa123db9ed79da51e68e86a | trade_date_block_shuffle | 10690 | BLOCKED | False | True | surrun_5eaf281547463765f25f6106 | UNDERPOWERED |
| sspec_dfa123db9ed79da51e68e86a | trade_date_block_shuffle | 10691 | BLOCKED | False | True | surrun_0169e4eb3355d46324f44669 | UNDERPOWERED |
| sspec_4b48ee8f1b16b3c796301091 | trade_date_block_shuffle | 10692 | BLOCKED | False | True | surrun_eaad21d60a0fc9cce5e3662a | UNDERPOWERED |
| sspec_4b48ee8f1b16b3c796301091 | trade_date_block_shuffle | 10693 | BLOCKED | False | True | surrun_b312213ac6fa36528ae7a8f0 | UNDERPOWERED |
| sspec_4b48ee8f1b16b3c796301091 | trade_date_block_shuffle | 10694 | BLOCKED | False | True | surrun_5afc1fb7b38e8482b9e734c6 | UNDERPOWERED |
| sspec_8c1f5685bf76f63f1918678f | trade_date_block_shuffle | 10695 | BLOCKED | False | True | surrun_3eabdfdde6a24fcd2da9b423 | UNDERPOWERED |
| sspec_8c1f5685bf76f63f1918678f | trade_date_block_shuffle | 10696 | BLOCKED | False | True | surrun_974aaa7a501dd1f85c31f390 | UNDERPOWERED |
| sspec_8c1f5685bf76f63f1918678f | trade_date_block_shuffle | 10697 | BLOCKED | False | True | surrun_33afd5458e7f73623d3fd596 | UNDERPOWERED |
| sspec_9466e5812145ed99c77addd8 | trade_date_block_shuffle | 10698 | BLOCKED | False | True | surrun_344bf49626a08bfc1848cde6 | UNDERPOWERED |
| sspec_9466e5812145ed99c77addd8 | trade_date_block_shuffle | 10699 | BLOCKED | False | True | surrun_675a83883233a29b1b88989d | UNDERPOWERED |
| sspec_9466e5812145ed99c77addd8 | trade_date_block_shuffle | 10700 | BLOCKED | False | True | surrun_c7496a680bf659daa09c4b99 | UNDERPOWERED |
| sspec_3bd847d9c68620974d8e4e58 | trade_date_block_shuffle | 10707 | BLOCKED | False | True | surrun_6dd4166b9cb7ab3ab12e6357 | UNDERPOWERED |
| sspec_3bd847d9c68620974d8e4e58 | trade_date_block_shuffle | 10708 | BLOCKED | False | True | surrun_a9c7a0572cb4d6b17f4ce78c | UNDERPOWERED |
| sspec_3bd847d9c68620974d8e4e58 | trade_date_block_shuffle | 10709 | BLOCKED | False | True | surrun_be9868f18d480415f73b9961 | UNDERPOWERED |
| sspec_86adf765160a896363bcd5b9 | trade_date_block_shuffle | 10710 | BLOCKED | False | True | surrun_ccac86df2dcc3defd7e10246 | UNDERPOWERED |
| sspec_86adf765160a896363bcd5b9 | trade_date_block_shuffle | 10711 | BLOCKED | False | True | surrun_435072cfed2e49c718c39d07 | UNDERPOWERED |
| sspec_86adf765160a896363bcd5b9 | trade_date_block_shuffle | 10712 | BLOCKED | False | True | surrun_ef8452e4a8b8f81a4c092008 | UNDERPOWERED |
| sspec_fd2750a3aca045563eb8af6b | trade_date_block_shuffle | 10713 | BLOCKED | False | False | surrun_49aef1bddcb18ef35843d5b3 | UNDERPOWERED |
| sspec_fd2750a3aca045563eb8af6b | trade_date_block_shuffle | 10714 | BLOCKED | False | False | surrun_d32459b2770a4a4f217e3cdc | UNDERPOWERED |
| sspec_fd2750a3aca045563eb8af6b | trade_date_block_shuffle | 10715 | BLOCKED | False | False | surrun_d9aafd70206bb26f51ff0102 | UNDERPOWERED |
| sspec_f80bd0be561d17e931fb0402 | trade_date_block_shuffle | 10716 | BLOCKED | False | True | surrun_c997adecc25d3de763895cfd | UNDERPOWERED |
| sspec_f80bd0be561d17e931fb0402 | trade_date_block_shuffle | 10717 | BLOCKED | False | True | surrun_caecb8ffcace4c994a19fb8a | UNDERPOWERED |
| sspec_f80bd0be561d17e931fb0402 | trade_date_block_shuffle | 10718 | BLOCKED | False | True | surrun_2c0d74268048e1d49be93f16 | UNDERPOWERED |
| sspec_a06280dea281704c1cdc37e0 | trade_date_block_shuffle | 10719 | BLOCKED | False | True | surrun_6b117b2af8f6053962a80443 | UNDERPOWERED |
| sspec_a06280dea281704c1cdc37e0 | trade_date_block_shuffle | 10720 | BLOCKED | False | True | surrun_7a23fff765187d115ec3558f | UNDERPOWERED |
| sspec_a06280dea281704c1cdc37e0 | trade_date_block_shuffle | 10721 | BLOCKED | False | True | surrun_2f4512b6541830f5998b9ccb | UNDERPOWERED |
| sspec_0990309cfb9e8788be5968f7 | trade_date_block_shuffle | 10722 | BLOCKED | False | True | surrun_dbe9243b2cd27b3c26d5bea5 | UNDERPOWERED |
| sspec_0990309cfb9e8788be5968f7 | trade_date_block_shuffle | 10723 | BLOCKED | False | True | surrun_d89769538efaba4178bd52c2 | UNDERPOWERED |
| sspec_0990309cfb9e8788be5968f7 | trade_date_block_shuffle | 10724 | BLOCKED | False | True | surrun_a8b4cf46b911735ec81a5d55 | UNDERPOWERED |
| sspec_0f9e9ad9bf8132b8922abe1f | trade_date_block_shuffle | 10725 | BLOCKED | False | True | surrun_f8017bcd4e8a71166feed72a | UNDERPOWERED |
| sspec_0f9e9ad9bf8132b8922abe1f | trade_date_block_shuffle | 10726 | BLOCKED | False | True | surrun_2cda94eff25bda1b844300ba | UNDERPOWERED |
| sspec_0f9e9ad9bf8132b8922abe1f | trade_date_block_shuffle | 10727 | BLOCKED | False | True | surrun_7ae8c428ea7efe571e3d19bc | UNDERPOWERED |
| sspec_d3a962c95c04c326a5a5b151 | trade_date_block_shuffle | 10728 | BLOCKED | False | True | surrun_dec1883311191003ad6df572 | UNDERPOWERED |
| sspec_d3a962c95c04c326a5a5b151 | trade_date_block_shuffle | 10729 | BLOCKED | False | True | surrun_6a494f38df2a38138e8d7504 | UNDERPOWERED |
| sspec_d3a962c95c04c326a5a5b151 | trade_date_block_shuffle | 10730 | BLOCKED | False | True | surrun_e5f6faf1a1a75b258cf4f56e | UNDERPOWERED |
| sspec_533ff382160faa39e06fcd0c | trade_date_block_shuffle | 10737 | BLOCKED | False | True | surrun_936eafd7294d3b2e6682d023 | UNDERPOWERED |
| sspec_533ff382160faa39e06fcd0c | trade_date_block_shuffle | 10738 | BLOCKED | False | True | surrun_80ca694aa258ebe348d0a964 | UNDERPOWERED |
| sspec_533ff382160faa39e06fcd0c | trade_date_block_shuffle | 10739 | BLOCKED | False | True | surrun_984176bf5753d72b3f855e5e | UNDERPOWERED |
| sspec_a65ba642712c610559cd9d3b | trade_date_block_shuffle | 10740 | BLOCKED | False | True | surrun_1fe76ce4b0fee787af282b4f | UNDERPOWERED |
| sspec_a65ba642712c610559cd9d3b | trade_date_block_shuffle | 10741 | BLOCKED | False | True | surrun_9d5bcdbb9eb10cea8d5eecf2 | UNDERPOWERED |
| sspec_a65ba642712c610559cd9d3b | trade_date_block_shuffle | 10742 | BLOCKED | False | True | surrun_318141f49a47103f20b3bb48 | UNDERPOWERED |
| sspec_03c63ff6b322f6f4909a78aa | trade_date_block_shuffle | 10743 | BLOCKED | False | True | surrun_243a4748ade281aa016f30a4 | UNDERPOWERED |
| sspec_03c63ff6b322f6f4909a78aa | trade_date_block_shuffle | 10744 | BLOCKED | False | True | surrun_887ca5dd5b1a330cc2b9c013 | UNDERPOWERED |
| sspec_03c63ff6b322f6f4909a78aa | trade_date_block_shuffle | 10745 | BLOCKED | False | True | surrun_2a8d3d09ddb8fd3472ce5ebe | UNDERPOWERED |
| sspec_2a34524e556fb66946af0adc | trade_date_block_shuffle | 10746 | BLOCKED | False | True | surrun_614375dee482009e9a2449cf | UNDERPOWERED |
| sspec_2a34524e556fb66946af0adc | trade_date_block_shuffle | 10747 | BLOCKED | False | True | surrun_33fb1c5d42206ecc09007502 | UNDERPOWERED |
| sspec_2a34524e556fb66946af0adc | trade_date_block_shuffle | 10748 | BLOCKED | False | True | surrun_9a178de7129e98e95b668cde | UNDERPOWERED |
| sspec_261125026ac6a6a550e5489e | trade_date_block_shuffle | 10749 | BLOCKED | False | True | surrun_275169fcc61f6378af6fbb9a | UNDERPOWERED |
| sspec_261125026ac6a6a550e5489e | trade_date_block_shuffle | 10750 | BLOCKED | False | True | surrun_e0ecc0cd9cb061730b6e65cc | UNDERPOWERED |
| sspec_261125026ac6a6a550e5489e | trade_date_block_shuffle | 10751 | BLOCKED | False | True | surrun_2376bf336b7b8db1853db752 | UNDERPOWERED |
| sspec_a0bc202daa195cc98c807f98 | trade_date_block_shuffle | 10752 | BLOCKED | False | True | surrun_46bb7efbcd44bdb24f8dc850 | UNDERPOWERED |
| sspec_a0bc202daa195cc98c807f98 | trade_date_block_shuffle | 10753 | BLOCKED | False | True | surrun_b2e0780f0490977540b217cd | UNDERPOWERED |
| sspec_a0bc202daa195cc98c807f98 | trade_date_block_shuffle | 10754 | BLOCKED | False | True | surrun_c0b8f9e79969c25e3150db76 | UNDERPOWERED |
| sspec_9f6259b2eea65e49428ab583 | trade_date_block_shuffle | 10755 | BLOCKED | False | True | surrun_a0de79ad7b7be77ff25d3d2e | UNDERPOWERED |
| sspec_9f6259b2eea65e49428ab583 | trade_date_block_shuffle | 10756 | BLOCKED | False | True | surrun_c427d2ea9e67d8283b5c382e | UNDERPOWERED |
| sspec_9f6259b2eea65e49428ab583 | trade_date_block_shuffle | 10757 | BLOCKED | False | True | surrun_ba76302a900e365af9796be8 | UNDERPOWERED |
| sspec_0b07a09019e3a1181159b0b5 | trade_date_block_shuffle | 10758 | BLOCKED | False | True | surrun_43a24d8f6b40492792fcca85 | UNDERPOWERED |
| sspec_0b07a09019e3a1181159b0b5 | trade_date_block_shuffle | 10759 | BLOCKED | False | True | surrun_b090adca6cfd981d70a879ea | UNDERPOWERED |
| sspec_0b07a09019e3a1181159b0b5 | trade_date_block_shuffle | 10760 | BLOCKED | False | True | surrun_72a7d627963b702c901f0ab3 | UNDERPOWERED |
| sspec_5d095928bc776ba1a0f11bd1 | trade_date_block_shuffle | 10767 | BLOCKED | False | True | surrun_62aae4e87c0ea28120a6ca5b | UNDERPOWERED |
| sspec_5d095928bc776ba1a0f11bd1 | trade_date_block_shuffle | 10768 | BLOCKED | False | True | surrun_61bab2f07ec4690475852ff4 | UNDERPOWERED |
| sspec_5d095928bc776ba1a0f11bd1 | trade_date_block_shuffle | 10769 | BLOCKED | False | True | surrun_996584021239a02c796cd870 | UNDERPOWERED |
| sspec_0c3a03aaf4a6e23d8dfd77ef | trade_date_block_shuffle | 10770 | BLOCKED | False | True | surrun_31ab6291a2722442a04985f8 | UNDERPOWERED |
| sspec_0c3a03aaf4a6e23d8dfd77ef | trade_date_block_shuffle | 10771 | BLOCKED | False | True | surrun_966391b5ecca56c0b245c301 | UNDERPOWERED |
| sspec_0c3a03aaf4a6e23d8dfd77ef | trade_date_block_shuffle | 10772 | BLOCKED | False | True | surrun_e1a3b27a2297213f310c9cb6 | UNDERPOWERED |
| sspec_326174687ccb2d68792ed3f0 | trade_date_block_shuffle | 10773 | BLOCKED | False | True | surrun_45c100c06273f7d422f41722 | UNDERPOWERED |
| sspec_326174687ccb2d68792ed3f0 | trade_date_block_shuffle | 10774 | BLOCKED | False | True | surrun_7e7883c0781cbe79dd9b28a1 | UNDERPOWERED |
| sspec_326174687ccb2d68792ed3f0 | trade_date_block_shuffle | 10775 | BLOCKED | False | True | surrun_4e033f7362d26bc254469daf | UNDERPOWERED |
| sspec_f8b2ab233a69231131a0c199 | trade_date_block_shuffle | 10776 | BLOCKED | False | True | surrun_3b57201202591c9afc81a729 | UNDERPOWERED |
| sspec_f8b2ab233a69231131a0c199 | trade_date_block_shuffle | 10777 | BLOCKED | False | True | surrun_7e8a1996b3e5d05458ef8f7b | UNDERPOWERED |
| sspec_f8b2ab233a69231131a0c199 | trade_date_block_shuffle | 10778 | BLOCKED | False | True | surrun_bd2dd51346ca9ee241813efb | UNDERPOWERED |
| sspec_5e855370880afb3f8f73bf76 | trade_date_block_shuffle | 10779 | BLOCKED | False | True | surrun_5b69c3307a745ef6f52eae02 | UNDERPOWERED |
| sspec_5e855370880afb3f8f73bf76 | trade_date_block_shuffle | 10780 | BLOCKED | False | True | surrun_bc6bbb92ebed8b7c53c98e14 | UNDERPOWERED |
| sspec_5e855370880afb3f8f73bf76 | trade_date_block_shuffle | 10781 | BLOCKED | False | True | surrun_e207af6e51a3d4d2a3d1368c | UNDERPOWERED |
| sspec_c1720272123b72b14c96e51c | trade_date_block_shuffle | 10782 | BLOCKED | False | True | surrun_acd2ef00fc84858c0b218a9d | UNDERPOWERED |
| sspec_c1720272123b72b14c96e51c | trade_date_block_shuffle | 10783 | BLOCKED | False | True | surrun_8637b6e49f8c378c7480062f | UNDERPOWERED |
| sspec_c1720272123b72b14c96e51c | trade_date_block_shuffle | 10784 | BLOCKED | False | True | surrun_2a8ba349fc981f22096469b4 | UNDERPOWERED |
| sspec_74285fdc388dd0840c14abda | trade_date_block_shuffle | 10785 | BLOCKED | False | True | surrun_1f7d513625b715d8080b40ac | UNDERPOWERED |
| sspec_74285fdc388dd0840c14abda | trade_date_block_shuffle | 10786 | BLOCKED | False | True | surrun_77c11188488a21a28d66da85 | UNDERPOWERED |
| sspec_74285fdc388dd0840c14abda | trade_date_block_shuffle | 10787 | BLOCKED | False | True | surrun_32c540f8e45cc3d8d7a47d37 | UNDERPOWERED |
| sspec_0260289769ca1a9d7496c1ab | trade_date_block_shuffle | 10788 | BLOCKED | False | True | surrun_7d6a8f9606219c1b4830835a | UNDERPOWERED |
| sspec_0260289769ca1a9d7496c1ab | trade_date_block_shuffle | 10789 | BLOCKED | False | True | surrun_e515aa08cb42a504ddb6de84 | UNDERPOWERED |
| sspec_0260289769ca1a9d7496c1ab | trade_date_block_shuffle | 10790 | BLOCKED | False | True | surrun_39e3bb1c492f5ebb5cc90304 | UNDERPOWERED |
| sspec_2449cfd728c761dbb4897c6e | trade_date_block_shuffle | 10791 | BLOCKED | False | True | surrun_cb3349ba5f23aff4399fd2f3 | UNDERPOWERED |
| sspec_2449cfd728c761dbb4897c6e | trade_date_block_shuffle | 10792 | BLOCKED | False | True | surrun_52921ed8608c20a3127b55b8 | UNDERPOWERED |
| sspec_2449cfd728c761dbb4897c6e | trade_date_block_shuffle | 10793 | BLOCKED | False | True | surrun_c7c57caed94a9e4889960cbd | UNDERPOWERED |
| sspec_684f569d85f1988a509d28df | trade_date_block_shuffle | 10797 | BLOCKED | False | True | surrun_1b1f0fcd1c59906568a41d4e | UNDERPOWERED |
| sspec_684f569d85f1988a509d28df | trade_date_block_shuffle | 10798 | BLOCKED | False | True | surrun_9c55f18e80333761448ab00c | UNDERPOWERED |
| sspec_684f569d85f1988a509d28df | trade_date_block_shuffle | 10799 | BLOCKED | False | True | surrun_61dcc3682e6c6f55a364bdcf | UNDERPOWERED |
| sspec_3afca631bbe2f9154d755d7b | trade_date_block_shuffle | 10800 | BLOCKED | False | True | surrun_e5b3964e1253ce07c84b7db8 | UNDERPOWERED |
| sspec_3afca631bbe2f9154d755d7b | trade_date_block_shuffle | 10801 | BLOCKED | False | True | surrun_7d1cb790896f6d2bf32696d4 | UNDERPOWERED |
| sspec_3afca631bbe2f9154d755d7b | trade_date_block_shuffle | 10802 | BLOCKED | False | True | surrun_446ca93d24462853718f6697 | UNDERPOWERED |
| sspec_419d162d9b178838f63fbba6 | trade_date_block_shuffle | 10803 | BLOCKED | False | True | surrun_c15a0a6d0126d21a6213a14c | UNDERPOWERED |
| sspec_419d162d9b178838f63fbba6 | trade_date_block_shuffle | 10804 | BLOCKED | False | True | surrun_b96c895475bc90350eea9fe8 | UNDERPOWERED |
| sspec_419d162d9b178838f63fbba6 | trade_date_block_shuffle | 10805 | BLOCKED | False | True | surrun_4fa639f9cd930a5ac614a3cb | UNDERPOWERED |
| sspec_110935b21bde6f964d90d4a7 | trade_date_block_shuffle | 10806 | BLOCKED | False | True | surrun_f34e80aac0fdcf07b575d956 | UNDERPOWERED |
| sspec_110935b21bde6f964d90d4a7 | trade_date_block_shuffle | 10807 | BLOCKED | False | True | surrun_b07cb63eb12a1a0c12540952 | UNDERPOWERED |
| sspec_110935b21bde6f964d90d4a7 | trade_date_block_shuffle | 10808 | BLOCKED | False | True | surrun_83a57caeda7508da58c207ad | UNDERPOWERED |
| sspec_33fcb8fb7b545b04a44b319d | trade_date_block_shuffle | 10809 | BLOCKED | False | True | surrun_49ae0d9dfb7b1e026bbafc89 | UNDERPOWERED |
| sspec_33fcb8fb7b545b04a44b319d | trade_date_block_shuffle | 10810 | BLOCKED | False | True | surrun_bfe2e508f5684006553eaf96 | UNDERPOWERED |
| sspec_33fcb8fb7b545b04a44b319d | trade_date_block_shuffle | 10811 | BLOCKED | False | True | surrun_c707d5a641b9e16ddc472073 | UNDERPOWERED |
| sspec_0d623cae8deb36756baca119 | trade_date_block_shuffle | 10812 | BLOCKED | False | True | surrun_81213106a8fba7b7c5a90b83 | UNDERPOWERED |
| sspec_0d623cae8deb36756baca119 | trade_date_block_shuffle | 10813 | BLOCKED | False | True | surrun_78b4de383a3dcfd8d2bb5fc3 | UNDERPOWERED |
| sspec_0d623cae8deb36756baca119 | trade_date_block_shuffle | 10814 | BLOCKED | False | True | surrun_e0f927a0ad82bf843a28b580 | UNDERPOWERED |
| sspec_258b8c65196e47840b4296de | trade_date_block_shuffle | 10815 | BLOCKED | False | True | surrun_0056139efa15d215af5a1ec5 | UNDERPOWERED |
| sspec_258b8c65196e47840b4296de | trade_date_block_shuffle | 10816 | BLOCKED | False | True | surrun_9da6bb32e8ad4da3a44b6feb | UNDERPOWERED |
| sspec_258b8c65196e47840b4296de | trade_date_block_shuffle | 10817 | BLOCKED | False | True | surrun_a6e8442fedef42973eb775f5 | UNDERPOWERED |
| sspec_33631390a4e6ed27b3c324f6 | trade_date_block_shuffle | 10818 | BLOCKED | False | True | surrun_d90c0fac3392329537e9faef | UNDERPOWERED |
| sspec_33631390a4e6ed27b3c324f6 | trade_date_block_shuffle | 10819 | BLOCKED | False | True | surrun_2f4f6ee0848009810bbd2e43 | UNDERPOWERED |
| sspec_33631390a4e6ed27b3c324f6 | trade_date_block_shuffle | 10820 | BLOCKED | False | True | surrun_c3227f05100affa9c7f5a86e | UNDERPOWERED |
| sspec_e28787de9a4e7464687e8697 | trade_date_block_shuffle | 10827 | BLOCKED | False | True | surrun_1f11438c8c040121ccaf7a0b | UNDERPOWERED |
| sspec_e28787de9a4e7464687e8697 | trade_date_block_shuffle | 10828 | BLOCKED | False | True | surrun_7bacf10d66fa1b24004d9ce8 | UNDERPOWERED |
| sspec_e28787de9a4e7464687e8697 | trade_date_block_shuffle | 10829 | BLOCKED | False | True | surrun_aaf6ced3b47e881e6679745a | UNDERPOWERED |
| sspec_74bd3bba2a9b74061e760954 | trade_date_block_shuffle | 10830 | BLOCKED | False | True | surrun_2182ec6c7b8a19af032e6f95 | UNDERPOWERED |
| sspec_74bd3bba2a9b74061e760954 | trade_date_block_shuffle | 10831 | BLOCKED | False | True | surrun_56c5f8993232d3fa1261c203 | UNDERPOWERED |
| sspec_74bd3bba2a9b74061e760954 | trade_date_block_shuffle | 10832 | BLOCKED | False | True | surrun_c3d117cb263f315a3f120292 | UNDERPOWERED |
| sspec_9908d0bed53f48739f812f9d | trade_date_block_shuffle | 10833 | BLOCKED | False | True | surrun_cc4893463c7be5eb19d01d9f | UNDERPOWERED |
| sspec_9908d0bed53f48739f812f9d | trade_date_block_shuffle | 10834 | BLOCKED | False | True | surrun_75796d8da937a869798485e3 | UNDERPOWERED |
| sspec_9908d0bed53f48739f812f9d | trade_date_block_shuffle | 10835 | BLOCKED | False | True | surrun_916c9ab243c4198e66705411 | UNDERPOWERED |
| sspec_b5521a0d1fd11a9d1844e00c | trade_date_block_shuffle | 10836 | BLOCKED | False | True | surrun_08e9c927a739b3720cde7344 | UNDERPOWERED |
| sspec_b5521a0d1fd11a9d1844e00c | trade_date_block_shuffle | 10837 | BLOCKED | False | True | surrun_0d3ac1a4b59b7c079ee2a65d | UNDERPOWERED |
| sspec_b5521a0d1fd11a9d1844e00c | trade_date_block_shuffle | 10838 | BLOCKED | False | True | surrun_0c7496d71f037df740a9d281 | UNDERPOWERED |
| sspec_1498f0d43ca61760f6f6955a | trade_date_block_shuffle | 10839 | BLOCKED | False | True | surrun_59268aff653328f4a1d36e89 | UNDERPOWERED |
| sspec_1498f0d43ca61760f6f6955a | trade_date_block_shuffle | 10840 | BLOCKED | False | True | surrun_54e61b11dfe65645f495e827 | UNDERPOWERED |
| sspec_1498f0d43ca61760f6f6955a | trade_date_block_shuffle | 10841 | BLOCKED | False | True | surrun_a8c3d0856ba02d5816b959be | UNDERPOWERED |
| sspec_9a9c79322b265c5f8129ed12 | trade_date_block_shuffle | 10842 | BLOCKED | False | True | surrun_c974db754db04283296a3785 | UNDERPOWERED |
| sspec_9a9c79322b265c5f8129ed12 | trade_date_block_shuffle | 10843 | BLOCKED | False | True | surrun_95875a029c645cec142840f8 | UNDERPOWERED |
| sspec_9a9c79322b265c5f8129ed12 | trade_date_block_shuffle | 10844 | BLOCKED | False | True | surrun_b5d9d8bcc158625406157c96 | UNDERPOWERED |
| sspec_9049fbde7d9bbd46c41f277c | trade_date_block_shuffle | 10845 | BLOCKED | False | True | surrun_2f108ba5c4ead0744de4a90f | UNDERPOWERED |
| sspec_9049fbde7d9bbd46c41f277c | trade_date_block_shuffle | 10846 | BLOCKED | False | True | surrun_112d2d805e94ec6416d1bc94 | UNDERPOWERED |
| sspec_9049fbde7d9bbd46c41f277c | trade_date_block_shuffle | 10847 | BLOCKED | False | True | surrun_3f25834487e4ae9df707bbd3 | UNDERPOWERED |
| sspec_1ac6a5e12e6a3eaaa7e3414c | trade_date_block_shuffle | 10848 | BLOCKED | False | True | surrun_da01a908646caca381de4623 | UNDERPOWERED |
| sspec_1ac6a5e12e6a3eaaa7e3414c | trade_date_block_shuffle | 10849 | BLOCKED | False | True | surrun_76d4716424020a7b541e506a | UNDERPOWERED |
| sspec_1ac6a5e12e6a3eaaa7e3414c | trade_date_block_shuffle | 10850 | BLOCKED | False | True | surrun_575346a3ee3ddc69db86463d | UNDERPOWERED |
| sspec_8657025ea76ba672da9865b2 | trade_date_block_shuffle | 10851 | BLOCKED | False | True | surrun_b13a70286b09122b9baef8e7 | UNDERPOWERED |
| sspec_8657025ea76ba672da9865b2 | trade_date_block_shuffle | 10852 | BLOCKED | False | True | surrun_a4bd1dd78bd874c86cf96241 | UNDERPOWERED |
| sspec_8657025ea76ba672da9865b2 | trade_date_block_shuffle | 10853 | BLOCKED | False | True | surrun_4613748ccb006db127c31adc | UNDERPOWERED |
| sspec_ac849ae4faf8a18a91083d1e | trade_date_block_shuffle | 10857 | BLOCKED | False | True | surrun_0ca48dfe34ec8920410c5511 | UNDERPOWERED |
| sspec_ac849ae4faf8a18a91083d1e | trade_date_block_shuffle | 10858 | BLOCKED | False | True | surrun_0a0d8a2d6e57821389a438a0 | UNDERPOWERED |
| sspec_ac849ae4faf8a18a91083d1e | trade_date_block_shuffle | 10859 | BLOCKED | False | True | surrun_edee5ba054a7e0580e1fd8a0 | UNDERPOWERED |
| sspec_f69c57c06e4a85a0125a7550 | trade_date_block_shuffle | 10860 | BLOCKED | False | True | surrun_c91d4922c2ed3aec06007c54 | UNDERPOWERED |
| sspec_f69c57c06e4a85a0125a7550 | trade_date_block_shuffle | 10861 | BLOCKED | False | True | surrun_aa9e3c4e59300bed0b39575c | UNDERPOWERED |
| sspec_f69c57c06e4a85a0125a7550 | trade_date_block_shuffle | 10862 | BLOCKED | False | True | surrun_18b51f734b35f7c35b0b8070 | UNDERPOWERED |
| sspec_46a94b704408745064e26d67 | trade_date_block_shuffle | 10863 | BLOCKED | False | True | surrun_773c83ec210d90b228b1707e | UNDERPOWERED |
| sspec_46a94b704408745064e26d67 | trade_date_block_shuffle | 10864 | BLOCKED | False | True | surrun_fa4250f688144546e8902ecf | UNDERPOWERED |
| sspec_46a94b704408745064e26d67 | trade_date_block_shuffle | 10865 | BLOCKED | False | True | surrun_1d327198b62da42d1c07131c | UNDERPOWERED |
| sspec_49511a9f49603b66d5d66c83 | trade_date_block_shuffle | 10866 | BLOCKED | False | True | surrun_7ac558dc4a2fa2c7eb0405f0 | UNDERPOWERED |
| sspec_49511a9f49603b66d5d66c83 | trade_date_block_shuffle | 10867 | BLOCKED | False | True | surrun_42fa8cfb89b209264f7ed5e5 | UNDERPOWERED |
| sspec_49511a9f49603b66d5d66c83 | trade_date_block_shuffle | 10868 | BLOCKED | False | True | surrun_065f560fb0aa4052ecf9d300 | UNDERPOWERED |
| sspec_fcf3c12b6e3e90ebd53933c5 | trade_date_block_shuffle | 10869 | BLOCKED | False | True | surrun_e53bd24c27d7919d8e12b9b8 | UNDERPOWERED |
| sspec_fcf3c12b6e3e90ebd53933c5 | trade_date_block_shuffle | 10870 | BLOCKED | False | True | surrun_57f885c096d06ccf4874f546 | UNDERPOWERED |
| sspec_fcf3c12b6e3e90ebd53933c5 | trade_date_block_shuffle | 10871 | BLOCKED | False | True | surrun_feee5fec71af774642291284 | UNDERPOWERED |
| sspec_be01b9679a0cd39454383b4d | trade_date_block_shuffle | 10872 | BLOCKED | False | True | surrun_ac0feeedd6d5a00dd6685d3e | UNDERPOWERED |
| sspec_be01b9679a0cd39454383b4d | trade_date_block_shuffle | 10873 | BLOCKED | False | True | surrun_bb3f09215d2ff245870da1d9 | UNDERPOWERED |
| sspec_be01b9679a0cd39454383b4d | trade_date_block_shuffle | 10874 | BLOCKED | False | True | surrun_0de1128e9173a1708a2a69c3 | UNDERPOWERED |
| sspec_4dd2be6e491ac64ff5a955be | trade_date_block_shuffle | 10875 | BLOCKED | False | True | surrun_70465e74ce1f94a98decd389 | UNDERPOWERED |
| sspec_4dd2be6e491ac64ff5a955be | trade_date_block_shuffle | 10876 | BLOCKED | False | True | surrun_a795fa15ce128e9bf53a7b7f | UNDERPOWERED |
| sspec_4dd2be6e491ac64ff5a955be | trade_date_block_shuffle | 10877 | BLOCKED | False | True | surrun_4b5f334341ae9049a0126084 | UNDERPOWERED |
| sspec_9815a44d3c2bcd03430deb87 | trade_date_block_shuffle | 10878 | BLOCKED | False | True | surrun_eeee87e70c9f18d3353c4089 | UNDERPOWERED |
| sspec_9815a44d3c2bcd03430deb87 | trade_date_block_shuffle | 10879 | BLOCKED | False | True | surrun_f72fea4b8eac4d236b10de7e | UNDERPOWERED |
| sspec_9815a44d3c2bcd03430deb87 | trade_date_block_shuffle | 10880 | BLOCKED | False | True | surrun_d00d489ac4e78b3bef0ac199 | UNDERPOWERED |
| sspec_2d39312d8d157477e82a8c6f | trade_date_block_shuffle | 10887 | BLOCKED | False | True | surrun_35d55090da20c8c66ca4252b | UNDERPOWERED |
| sspec_2d39312d8d157477e82a8c6f | trade_date_block_shuffle | 10888 | BLOCKED | False | True | surrun_9540da147b5872c39af0cddd | UNDERPOWERED |
| sspec_2d39312d8d157477e82a8c6f | trade_date_block_shuffle | 10889 | BLOCKED | False | True | surrun_56faf3461006550357259adf | UNDERPOWERED |
| sspec_0d786a51a32f55701d86cc9b | trade_date_block_shuffle | 10890 | BLOCKED | False | True | surrun_9e722ce6322fa6d3507cd804 | UNDERPOWERED |
| sspec_0d786a51a32f55701d86cc9b | trade_date_block_shuffle | 10891 | BLOCKED | False | True | surrun_d7372a0331e7544a703e477b | UNDERPOWERED |
| sspec_0d786a51a32f55701d86cc9b | trade_date_block_shuffle | 10892 | BLOCKED | False | True | surrun_bcf1f8a708d9e6e00a76b262 | UNDERPOWERED |
| sspec_691e00c3a46428a3157d8ec1 | trade_date_block_shuffle | 10893 | BLOCKED | False | True | surrun_9c8dbcb9e871a32a77fb312b | UNDERPOWERED |
| sspec_691e00c3a46428a3157d8ec1 | trade_date_block_shuffle | 10894 | BLOCKED | False | True | surrun_217ff360011a0107898ea4a2 | UNDERPOWERED |
| sspec_691e00c3a46428a3157d8ec1 | trade_date_block_shuffle | 10895 | BLOCKED | False | True | surrun_0418dc111ef12d6e58addc93 | UNDERPOWERED |
| sspec_7e696c51356012e9433a9108 | trade_date_block_shuffle | 10896 | BLOCKED | False | True | surrun_a49fd4944c8cc96adb90f9c0 | UNDERPOWERED |
| sspec_7e696c51356012e9433a9108 | trade_date_block_shuffle | 10897 | BLOCKED | False | True | surrun_72fb042489381e51f9353fd7 | UNDERPOWERED |
| sspec_7e696c51356012e9433a9108 | trade_date_block_shuffle | 10898 | BLOCKED | False | True | surrun_c4039fe774e56c2b83458cd9 | UNDERPOWERED |
| sspec_65975eb5177404e4e861011c | trade_date_block_shuffle | 10899 | BLOCKED | False | True | surrun_b843b856a2e758acf9f565fd | UNDERPOWERED |
| sspec_65975eb5177404e4e861011c | trade_date_block_shuffle | 10900 | BLOCKED | False | True | surrun_c6d49d0a1f525d4b8b4944e3 | UNDERPOWERED |
| sspec_65975eb5177404e4e861011c | trade_date_block_shuffle | 10901 | BLOCKED | False | True | surrun_372d55cca7fde8d64a54080d | UNDERPOWERED |
| sspec_82772f708fb53fb992481605 | trade_date_block_shuffle | 10902 | BLOCKED | False | True | surrun_de7cd57b1422c76c2ea4b467 | UNDERPOWERED |
| sspec_82772f708fb53fb992481605 | trade_date_block_shuffle | 10903 | BLOCKED | False | True | surrun_99e46e93faa778583174482f | UNDERPOWERED |
| sspec_82772f708fb53fb992481605 | trade_date_block_shuffle | 10904 | BLOCKED | False | True | surrun_1daad8b060a227fd1ea85312 | UNDERPOWERED |
| sspec_d2a04824cab2216f85e4b8c7 | trade_date_block_shuffle | 10905 | BLOCKED | False | True | surrun_d9937d2a0f2b3f4829ad07d4 | UNDERPOWERED |
| sspec_d2a04824cab2216f85e4b8c7 | trade_date_block_shuffle | 10906 | BLOCKED | False | True | surrun_85a87f654f923087253a719b | UNDERPOWERED |
| sspec_d2a04824cab2216f85e4b8c7 | trade_date_block_shuffle | 10907 | BLOCKED | False | True | surrun_b74fab29bda4515ceaefab5c | UNDERPOWERED |
| sspec_95e8550f25151503fd62881a | trade_date_block_shuffle | 10908 | BLOCKED | False | True | surrun_cc6a2c2aced9d6f6a8b2ab6e | UNDERPOWERED |
| sspec_95e8550f25151503fd62881a | trade_date_block_shuffle | 10909 | BLOCKED | False | True | surrun_59b464d53013e371bd933798 | UNDERPOWERED |
| sspec_95e8550f25151503fd62881a | trade_date_block_shuffle | 10910 | BLOCKED | False | True | surrun_85fc92b959a9122bc8145b27 | UNDERPOWERED |
| sspec_cad600c7e7ae82ee371f300d | trade_date_block_shuffle | 10917 | BLOCKED | False | True | surrun_1fc2194f711557dfffdb2c62 | UNDERPOWERED |
| sspec_cad600c7e7ae82ee371f300d | trade_date_block_shuffle | 10918 | BLOCKED | False | True | surrun_48ebd84270a664d5371ccf0d | UNDERPOWERED |
| sspec_cad600c7e7ae82ee371f300d | trade_date_block_shuffle | 10919 | BLOCKED | False | True | surrun_9dcf9f6bdfbf1dcc7227c409 | UNDERPOWERED |
| sspec_393c8161beb74ba83f5a164b | trade_date_block_shuffle | 10920 | BLOCKED | False | True | surrun_a9a6921cbd41eb4912dc5f8d | UNDERPOWERED |
| sspec_393c8161beb74ba83f5a164b | trade_date_block_shuffle | 10921 | BLOCKED | False | True | surrun_3f8b6310865d8eba850be9a9 | UNDERPOWERED |
| sspec_393c8161beb74ba83f5a164b | trade_date_block_shuffle | 10922 | BLOCKED | False | True | surrun_29dc5033c20c312f1fcd3ea4 | UNDERPOWERED |
| sspec_974ff4d3b7738064e6dff75f | trade_date_block_shuffle | 10923 | BLOCKED | False | True | surrun_809c860d95137b4572041ce1 | UNDERPOWERED |
| sspec_974ff4d3b7738064e6dff75f | trade_date_block_shuffle | 10924 | BLOCKED | False | True | surrun_ddadb9dc114ba8b6cbcc9414 | UNDERPOWERED |
| sspec_974ff4d3b7738064e6dff75f | trade_date_block_shuffle | 10925 | BLOCKED | False | True | surrun_0bf0494bf2382ea719303fcd | UNDERPOWERED |
| sspec_df4c90ce1bae0acccd4d13d9 | trade_date_block_shuffle | 10926 | BLOCKED | False | True | surrun_e5da2eed687e98d3284679b5 | UNDERPOWERED |
| sspec_df4c90ce1bae0acccd4d13d9 | trade_date_block_shuffle | 10927 | BLOCKED | False | True | surrun_79b3aca35839a9395b3da18f | UNDERPOWERED |
| sspec_df4c90ce1bae0acccd4d13d9 | trade_date_block_shuffle | 10928 | BLOCKED | False | True | surrun_60c3b9e6123567222c1643ae | UNDERPOWERED |
| sspec_3b888310b6e62e8b4aa4f581 | trade_date_block_shuffle | 10929 | BLOCKED | False | True | surrun_bcabe0ec26b07a6a5a499de4 | UNDERPOWERED |
| sspec_3b888310b6e62e8b4aa4f581 | trade_date_block_shuffle | 10930 | BLOCKED | False | True | surrun_ba3538da1b9f204e1b0893e8 | UNDERPOWERED |
| sspec_3b888310b6e62e8b4aa4f581 | trade_date_block_shuffle | 10931 | BLOCKED | False | True | surrun_a121f8cfcc7087bed021dcc4 | UNDERPOWERED |
| sspec_0501ae1937d72076f88c76aa | trade_date_block_shuffle | 10932 | BLOCKED | False | True | surrun_ef5b3a5ae67105cfb18a9b97 | UNDERPOWERED |
| sspec_0501ae1937d72076f88c76aa | trade_date_block_shuffle | 10933 | BLOCKED | False | True | surrun_7fa5d6e9b09d4d77b47e16fa | UNDERPOWERED |
| sspec_0501ae1937d72076f88c76aa | trade_date_block_shuffle | 10934 | BLOCKED | False | True | surrun_98607a5cf127af991fe878cb | UNDERPOWERED |
| sspec_64628498470d067426f90bc7 | trade_date_block_shuffle | 10935 | BLOCKED | False | True | surrun_62ffa5584cbd0ab2a7e870c8 | UNDERPOWERED |
| sspec_64628498470d067426f90bc7 | trade_date_block_shuffle | 10936 | BLOCKED | False | True | surrun_0c799610b048f640f04f5e82 | UNDERPOWERED |
| sspec_64628498470d067426f90bc7 | trade_date_block_shuffle | 10937 | BLOCKED | False | True | surrun_fecf029129b71ae7531fc7be | UNDERPOWERED |
| sspec_818ff30a836a7109b0197261 | trade_date_block_shuffle | 10938 | BLOCKED | False | True | surrun_7d37c7ea876770d5af7820f3 | UNDERPOWERED |
| sspec_818ff30a836a7109b0197261 | trade_date_block_shuffle | 10939 | BLOCKED | False | True | surrun_7f30dce152ed71f5f367f1b6 | UNDERPOWERED |
| sspec_818ff30a836a7109b0197261 | trade_date_block_shuffle | 10940 | BLOCKED | False | True | surrun_a70c0b82f753d51e462ae34c | UNDERPOWERED |
| sspec_61916013e1c79796eb3a2b70 | trade_date_block_shuffle | 10947 | BLOCKED | False | True | surrun_31482aab113e244571cea1cf | UNDERPOWERED |
| sspec_61916013e1c79796eb3a2b70 | trade_date_block_shuffle | 10948 | BLOCKED | False | True | surrun_7c255983f32536cbee62132e | UNDERPOWERED |
| sspec_61916013e1c79796eb3a2b70 | trade_date_block_shuffle | 10949 | BLOCKED | False | True | surrun_32f9ddf47b9e0351a1ba610c | UNDERPOWERED |
| sspec_2c45062ddc0fd1c1fd6d5659 | trade_date_block_shuffle | 10950 | BLOCKED | False | True | surrun_4f1bb587f1bf9ffd3db12b1f | UNDERPOWERED |
| sspec_2c45062ddc0fd1c1fd6d5659 | trade_date_block_shuffle | 10951 | BLOCKED | False | True | surrun_810646e7223640e5a42f5230 | UNDERPOWERED |
| sspec_2c45062ddc0fd1c1fd6d5659 | trade_date_block_shuffle | 10952 | BLOCKED | False | True | surrun_ca24a88ebbd8ffcf6db1cbd4 | UNDERPOWERED |
| sspec_7b23272b2bfb00ace9f93c9d | trade_date_block_shuffle | 10953 | BLOCKED | False | True | surrun_36cead1056afd820e646daf8 | UNDERPOWERED |
| sspec_7b23272b2bfb00ace9f93c9d | trade_date_block_shuffle | 10954 | BLOCKED | False | True | surrun_cd8b8adf5606b43c20ce6cf3 | UNDERPOWERED |
| sspec_7b23272b2bfb00ace9f93c9d | trade_date_block_shuffle | 10955 | BLOCKED | False | True | surrun_628832e778b1f166b9733288 | UNDERPOWERED |
| sspec_eccb7e90a6240aca1907d921 | trade_date_block_shuffle | 10956 | BLOCKED | False | True | surrun_012bd076b9915e9a74a8a00f | UNDERPOWERED |
| sspec_eccb7e90a6240aca1907d921 | trade_date_block_shuffle | 10957 | BLOCKED | False | True | surrun_c6a50e4320b10f2d7b5a6d55 | UNDERPOWERED |
| sspec_eccb7e90a6240aca1907d921 | trade_date_block_shuffle | 10958 | BLOCKED | False | True | surrun_4e9e1e0f51044503279105c1 | UNDERPOWERED |
| sspec_0c5f89a5241378dea3b88500 | trade_date_block_shuffle | 10959 | BLOCKED | False | True | surrun_5bd0a713792ffd500c6c66e0 | UNDERPOWERED |
| sspec_0c5f89a5241378dea3b88500 | trade_date_block_shuffle | 10960 | BLOCKED | False | True | surrun_e099fb47b1643027ff502387 | UNDERPOWERED |
| sspec_0c5f89a5241378dea3b88500 | trade_date_block_shuffle | 10961 | BLOCKED | False | True | surrun_be272208565146db177f081e | UNDERPOWERED |
| sspec_1c10af416dbef79d161428fa | trade_date_block_shuffle | 10962 | BLOCKED | False | True | surrun_cdaa497d345469ff7ab8a01d | UNDERPOWERED |
| sspec_1c10af416dbef79d161428fa | trade_date_block_shuffle | 10963 | BLOCKED | False | True | surrun_1890c30431d77deaa8bb7fa2 | UNDERPOWERED |
| sspec_1c10af416dbef79d161428fa | trade_date_block_shuffle | 10964 | BLOCKED | False | True | surrun_f8bb4d0f040780ba4832b310 | UNDERPOWERED |
| sspec_41cb322e5ba5146a0e377c35 | trade_date_block_shuffle | 10965 | BLOCKED | False | True | surrun_2eb233ed5c19590f4055b088 | UNDERPOWERED |
| sspec_41cb322e5ba5146a0e377c35 | trade_date_block_shuffle | 10966 | BLOCKED | False | True | surrun_511b06e48bca91029d41a5c7 | UNDERPOWERED |
| sspec_41cb322e5ba5146a0e377c35 | trade_date_block_shuffle | 10967 | BLOCKED | False | True | surrun_15363e933d447c92b3fa9617 | UNDERPOWERED |
| sspec_5f738d58e8c7cbb1044d4531 | trade_date_block_shuffle | 10968 | BLOCKED | False | True | surrun_c59fd3e364cb26790524f470 | UNDERPOWERED |
| sspec_5f738d58e8c7cbb1044d4531 | trade_date_block_shuffle | 10969 | BLOCKED | False | True | surrun_657f9a408033b347064ef0dd | UNDERPOWERED |
| sspec_5f738d58e8c7cbb1044d4531 | trade_date_block_shuffle | 10970 | BLOCKED | False | True | surrun_5666b05cc2b67683df11b93b | UNDERPOWERED |
| sspec_0c843327bc4db32869d60670 | trade_date_block_shuffle | 10977 | BLOCKED | False | True | surrun_1c4a0e16ed4058513e278577 | UNDERPOWERED |
| sspec_0c843327bc4db32869d60670 | trade_date_block_shuffle | 10978 | BLOCKED | False | True | surrun_7df13510e2735efa6e1277c8 | UNDERPOWERED |
| sspec_0c843327bc4db32869d60670 | trade_date_block_shuffle | 10979 | BLOCKED | False | True | surrun_84bac343748f2b217fdf76b5 | UNDERPOWERED |
| sspec_24ccd2d37bab9f3af31a4837 | trade_date_block_shuffle | 10980 | BLOCKED | False | True | surrun_c60deb5c127f913835526820 | UNDERPOWERED |
| sspec_24ccd2d37bab9f3af31a4837 | trade_date_block_shuffle | 10981 | BLOCKED | False | True | surrun_82a450754e02204d0a54ca6e | UNDERPOWERED |
| sspec_24ccd2d37bab9f3af31a4837 | trade_date_block_shuffle | 10982 | BLOCKED | False | True | surrun_0386f3d84ce91eaac179c9c8 | UNDERPOWERED |
| sspec_070f899e3376d506f37a514b | trade_date_block_shuffle | 10983 | BLOCKED | False | True | surrun_a451e0e4096d846655a2b590 | UNDERPOWERED |
| sspec_070f899e3376d506f37a514b | trade_date_block_shuffle | 10984 | BLOCKED | False | True | surrun_826cd5afee1d8f314619afc2 | UNDERPOWERED |
| sspec_070f899e3376d506f37a514b | trade_date_block_shuffle | 10985 | BLOCKED | False | True | surrun_67f5f6d1c05b548f1abeb975 | UNDERPOWERED |
| sspec_c5eb834b3c0c2da9102e1bf0 | trade_date_block_shuffle | 10986 | BLOCKED | False | True | surrun_b2d1d242ccd7b447194568b3 | UNDERPOWERED |
| sspec_c5eb834b3c0c2da9102e1bf0 | trade_date_block_shuffle | 10987 | BLOCKED | False | True | surrun_ba46c91236a3c29e3d99dd05 | UNDERPOWERED |
| sspec_c5eb834b3c0c2da9102e1bf0 | trade_date_block_shuffle | 10988 | BLOCKED | False | True | surrun_13bd7d69c04259ebd87c2afd | UNDERPOWERED |
| sspec_27a6973546c9dbee1895c59e | trade_date_block_shuffle | 10989 | BLOCKED | False | True | surrun_f4edffd24f5279a1204b749c | UNDERPOWERED |
| sspec_27a6973546c9dbee1895c59e | trade_date_block_shuffle | 10990 | BLOCKED | False | True | surrun_35a3801f972104025a17e779 | UNDERPOWERED |
| sspec_27a6973546c9dbee1895c59e | trade_date_block_shuffle | 10991 | BLOCKED | False | True | surrun_531915222154422f2d680ac5 | UNDERPOWERED |
| sspec_6f00aad98600d03ac168ec59 | trade_date_block_shuffle | 10992 | BLOCKED | False | True | surrun_91cac5aa69e3b425a6448e19 | UNDERPOWERED |
| sspec_6f00aad98600d03ac168ec59 | trade_date_block_shuffle | 10993 | BLOCKED | False | True | surrun_f5c60ec198df7fac3eca9e0b | UNDERPOWERED |
| sspec_6f00aad98600d03ac168ec59 | trade_date_block_shuffle | 10994 | BLOCKED | False | True | surrun_bd0349c4c8db475740f8d813 | UNDERPOWERED |
| sspec_18babac6084336d9e0d0354f | trade_date_block_shuffle | 11007 | BLOCKED | False | True | surrun_773478bde2eecbfa815f06df | UNDERPOWERED |
| sspec_18babac6084336d9e0d0354f | trade_date_block_shuffle | 11008 | BLOCKED | False | True | surrun_b466559a359b7c6db734c84f | UNDERPOWERED |
| sspec_18babac6084336d9e0d0354f | trade_date_block_shuffle | 11009 | BLOCKED | False | True | surrun_52498044e96e0225599cdf73 | UNDERPOWERED |
| sspec_3c850fb9543b35da6dc851ed | trade_date_block_shuffle | 11010 | BLOCKED | False | True | surrun_5ecb1817eba5127e7c26fbe1 | UNDERPOWERED |
| sspec_3c850fb9543b35da6dc851ed | trade_date_block_shuffle | 11011 | BLOCKED | False | True | surrun_b7b2bab5584cd198c32145a2 | UNDERPOWERED |
| sspec_3c850fb9543b35da6dc851ed | trade_date_block_shuffle | 11012 | BLOCKED | False | True | surrun_26e6dca2d02d7562030be652 | UNDERPOWERED |
| sspec_d8631bd19935f7ce41733cb9 | trade_date_block_shuffle | 11013 | BLOCKED | False | True | surrun_fc3f0ac2cdc9e01adcfb98d5 | UNDERPOWERED |
| sspec_d8631bd19935f7ce41733cb9 | trade_date_block_shuffle | 11014 | BLOCKED | False | True | surrun_2cad0994eaa6dd5fdfc12acf | UNDERPOWERED |
| sspec_d8631bd19935f7ce41733cb9 | trade_date_block_shuffle | 11015 | BLOCKED | False | True | surrun_6f10d129ce86f8c8763eaae3 | UNDERPOWERED |
| sspec_3a2b5f926d2788acbb0458fb | trade_date_block_shuffle | 11016 | BLOCKED | False | True | surrun_2bbd017fcb45585a04a6077b | UNDERPOWERED |
| sspec_3a2b5f926d2788acbb0458fb | trade_date_block_shuffle | 11017 | BLOCKED | False | True | surrun_17478b8712e76f8bd8d747a6 | UNDERPOWERED |
| sspec_3a2b5f926d2788acbb0458fb | trade_date_block_shuffle | 11018 | BLOCKED | False | True | surrun_7ea63629aeb7ed16d8861de5 | UNDERPOWERED |
| sspec_b4590e215f35a7ed9a143b3e | trade_date_block_shuffle | 11019 | BLOCKED | False | True | surrun_2cc655b1ad04953a511528f8 | UNDERPOWERED |
| sspec_b4590e215f35a7ed9a143b3e | trade_date_block_shuffle | 11020 | BLOCKED | False | True | surrun_f725c084dc7d912a9dd735d3 | UNDERPOWERED |
| sspec_b4590e215f35a7ed9a143b3e | trade_date_block_shuffle | 11021 | BLOCKED | False | True | surrun_9120ab2c0e56e202ecc34786 | UNDERPOWERED |
| sspec_a4eab43fc2a064ff857ad0fa | trade_date_block_shuffle | 11022 | BLOCKED | False | True | surrun_4f00389bd0d31aca09362c5f | UNDERPOWERED |
| sspec_a4eab43fc2a064ff857ad0fa | trade_date_block_shuffle | 11023 | BLOCKED | False | True | surrun_43320c432273811b17d0b764 | UNDERPOWERED |
| sspec_a4eab43fc2a064ff857ad0fa | trade_date_block_shuffle | 11024 | BLOCKED | False | True | surrun_cbbd3da56fd7e03173adf74b | UNDERPOWERED |
| sspec_babef3f82448347395278c8a | trade_date_block_shuffle | 11025 | BLOCKED | False | True | surrun_0e741b090e0c910751296e56 | UNDERPOWERED |
| sspec_babef3f82448347395278c8a | trade_date_block_shuffle | 11026 | BLOCKED | False | True | surrun_5f723aad59a6d0b3791e7d59 | UNDERPOWERED |
| sspec_babef3f82448347395278c8a | trade_date_block_shuffle | 11027 | BLOCKED | False | True | surrun_5b5a54d7d1710ba8344937a7 | UNDERPOWERED |
| sspec_b51d27525273a2d7b303e330 | trade_date_block_shuffle | 11028 | BLOCKED | False | True | surrun_e8a88cc0f19a3dcec044ad0d | UNDERPOWERED |
| sspec_b51d27525273a2d7b303e330 | trade_date_block_shuffle | 11029 | BLOCKED | False | True | surrun_b0f34c1216e3f357c1742342 | UNDERPOWERED |
| sspec_b51d27525273a2d7b303e330 | trade_date_block_shuffle | 11030 | BLOCKED | False | True | surrun_a274fe774a2c86020de7f0c5 | UNDERPOWERED |
| sspec_1691b58a41a69cb8e3f69d49 | trade_date_block_shuffle | 11031 | BLOCKED | False | True | surrun_be3609b1af7dc87528e6a535 | UNDERPOWERED |
| sspec_1691b58a41a69cb8e3f69d49 | trade_date_block_shuffle | 11032 | BLOCKED | False | True | surrun_7fa95f5eb35b014ee3f72710 | UNDERPOWERED |
| sspec_1691b58a41a69cb8e3f69d49 | trade_date_block_shuffle | 11033 | BLOCKED | False | True | surrun_c5a848c4852d6746979beaee | UNDERPOWERED |
| sspec_129c4e401bd8ed5ea1955513 | trade_date_block_shuffle | 11037 | BLOCKED | False | True | surrun_27962ca8a23f34b9139598e6 | UNDERPOWERED |
| sspec_129c4e401bd8ed5ea1955513 | trade_date_block_shuffle | 11038 | BLOCKED | False | True | surrun_1e37f7548d55ce236c8768f2 | UNDERPOWERED |
| sspec_129c4e401bd8ed5ea1955513 | trade_date_block_shuffle | 11039 | BLOCKED | False | True | surrun_a59b804c6e34e5d892b73359 | UNDERPOWERED |
| sspec_8457b52fb12ffc506c5c268c | trade_date_block_shuffle | 11040 | BLOCKED | False | True | surrun_e66c80bd544a1745b24709e9 | UNDERPOWERED |
| sspec_8457b52fb12ffc506c5c268c | trade_date_block_shuffle | 11041 | BLOCKED | False | True | surrun_942ec373d422ded718293e86 | UNDERPOWERED |
| sspec_8457b52fb12ffc506c5c268c | trade_date_block_shuffle | 11042 | BLOCKED | False | True | surrun_bbaf6053a0e5d38eef817651 | UNDERPOWERED |
| sspec_6f50f372725077248326de08 | trade_date_block_shuffle | 11043 | BLOCKED | False | True | surrun_0cdc142275a3446e5ff5f9a3 | UNDERPOWERED |
| sspec_6f50f372725077248326de08 | trade_date_block_shuffle | 11044 | BLOCKED | False | True | surrun_415a0bd69fce4ef71667b704 | UNDERPOWERED |
| sspec_6f50f372725077248326de08 | trade_date_block_shuffle | 11045 | BLOCKED | False | True | surrun_ea46238628d3f0436aec6abd | UNDERPOWERED |
| sspec_d03c10259d8962fcd9c88d8c | trade_date_block_shuffle | 11046 | BLOCKED | False | True | surrun_2ecba8b2c015d3d02ece2e1c | UNDERPOWERED |
| sspec_d03c10259d8962fcd9c88d8c | trade_date_block_shuffle | 11047 | BLOCKED | False | True | surrun_d634052fcde0b1bfec42d1ea | UNDERPOWERED |
| sspec_d03c10259d8962fcd9c88d8c | trade_date_block_shuffle | 11048 | BLOCKED | False | True | surrun_b8df4f4042396954c42db861 | UNDERPOWERED |
| sspec_15cdf921185c6c5c92cc08ea | trade_date_block_shuffle | 11049 | BLOCKED | False | True | surrun_91431f61e8edeab28bba90dc | UNDERPOWERED |
| sspec_15cdf921185c6c5c92cc08ea | trade_date_block_shuffle | 11050 | BLOCKED | False | True | surrun_2d3d54d7b87d4f74c2b1a60e | UNDERPOWERED |
| sspec_15cdf921185c6c5c92cc08ea | trade_date_block_shuffle | 11051 | BLOCKED | False | True | surrun_492ba7b13e771137420789f8 | UNDERPOWERED |
| sspec_920ecdc185f4bcfac4c1034b | trade_date_block_shuffle | 11052 | BLOCKED | False | True | surrun_2e9a9d5f11d99fcf5ca61897 | UNDERPOWERED |
| sspec_920ecdc185f4bcfac4c1034b | trade_date_block_shuffle | 11053 | BLOCKED | False | True | surrun_508983a7b7724cf2dda741d3 | UNDERPOWERED |
| sspec_920ecdc185f4bcfac4c1034b | trade_date_block_shuffle | 11054 | BLOCKED | False | True | surrun_9a3a8f4403baddc122244e5f | UNDERPOWERED |
| sspec_d634d75a4167211ac0e4e1ad | trade_date_block_shuffle | 11067 | BLOCKED | False | True | surrun_05b33e18fc3728c04fdc8b20 | UNDERPOWERED |
| sspec_d634d75a4167211ac0e4e1ad | trade_date_block_shuffle | 11068 | BLOCKED | False | True | surrun_6a2eb8cf9df832ed1b41d07c | UNDERPOWERED |
| sspec_d634d75a4167211ac0e4e1ad | trade_date_block_shuffle | 11069 | BLOCKED | False | True | surrun_eed5f0339accdd6d00ff1f21 | UNDERPOWERED |
| sspec_916eb81b66236f6b0c878b8c | trade_date_block_shuffle | 11070 | BLOCKED | False | True | surrun_34c30e672e76a02c21cc3db7 | UNDERPOWERED |
| sspec_916eb81b66236f6b0c878b8c | trade_date_block_shuffle | 11071 | BLOCKED | False | True | surrun_5ea59a165418e45c000fc7c4 | UNDERPOWERED |
| sspec_916eb81b66236f6b0c878b8c | trade_date_block_shuffle | 11072 | BLOCKED | False | True | surrun_95a07c566a1362b1f3c63a31 | UNDERPOWERED |
| sspec_297660383d7daa6b9894ba8d | trade_date_block_shuffle | 11073 | BLOCKED | False | True | surrun_36f7cf4b2012ebadece140be | UNDERPOWERED |
| sspec_297660383d7daa6b9894ba8d | trade_date_block_shuffle | 11074 | BLOCKED | False | True | surrun_fcc6d4734356688a0e611285 | UNDERPOWERED |
| sspec_297660383d7daa6b9894ba8d | trade_date_block_shuffle | 11075 | BLOCKED | False | True | surrun_f89cd62fbca41190f6829e95 | UNDERPOWERED |
| sspec_2ec6d059219c2609e5b4f9ee | trade_date_block_shuffle | 11076 | BLOCKED | False | True | surrun_14a254f27acad90832cfd419 | UNDERPOWERED |
| sspec_2ec6d059219c2609e5b4f9ee | trade_date_block_shuffle | 11077 | BLOCKED | False | True | surrun_d9a7a5598bd280d8cb859484 | UNDERPOWERED |
| sspec_2ec6d059219c2609e5b4f9ee | trade_date_block_shuffle | 11078 | BLOCKED | False | True | surrun_534dddbe6fe79959cd552f4f | UNDERPOWERED |
| sspec_1339b6ccd0c986f06cccb4ab | trade_date_block_shuffle | 11079 | BLOCKED | False | True | surrun_190fa7c4ce8d44151c2c899d | UNDERPOWERED |
| sspec_1339b6ccd0c986f06cccb4ab | trade_date_block_shuffle | 11080 | BLOCKED | False | True | surrun_b3ca544ac7f3d121a53ad63c | UNDERPOWERED |
| sspec_1339b6ccd0c986f06cccb4ab | trade_date_block_shuffle | 11081 | BLOCKED | False | True | surrun_245e84c283c2e6c53565cc5b | UNDERPOWERED |
| sspec_7624adbe7f648eab89a8a3a8 | trade_date_block_shuffle | 11082 | BLOCKED | False | True | surrun_cc4f0e27d44bce20120ab943 | UNDERPOWERED |
| sspec_7624adbe7f648eab89a8a3a8 | trade_date_block_shuffle | 11083 | BLOCKED | False | True | surrun_01cf4b6716c7b803af4f0494 | UNDERPOWERED |
| sspec_7624adbe7f648eab89a8a3a8 | trade_date_block_shuffle | 11084 | BLOCKED | False | True | surrun_59a734e421afd5d9c23f9858 | UNDERPOWERED |
| sspec_487ba6544a769ba29031817d | trade_date_block_shuffle | 11085 | BLOCKED | False | True | surrun_64404748325f15ccc6bfc7e2 | UNDERPOWERED |
| sspec_487ba6544a769ba29031817d | trade_date_block_shuffle | 11086 | BLOCKED | False | True | surrun_caed9946b02326dee7a00166 | UNDERPOWERED |
| sspec_487ba6544a769ba29031817d | trade_date_block_shuffle | 11087 | BLOCKED | False | True | surrun_be5fc99f0a72c19ce8f326e9 | UNDERPOWERED |
| sspec_1d9845045f6c42cb331d1d1f | trade_date_block_shuffle | 11088 | BLOCKED | False | True | surrun_0910e8712fb8dc8bf796f774 | UNDERPOWERED |
| sspec_1d9845045f6c42cb331d1d1f | trade_date_block_shuffle | 11089 | BLOCKED | False | True | surrun_94e10f4f3a098441beb9e97c | UNDERPOWERED |
| sspec_1d9845045f6c42cb331d1d1f | trade_date_block_shuffle | 11090 | BLOCKED | False | True | surrun_abf997fb52620462b1c51b31 | UNDERPOWERED |
| sspec_49c83645a3956da01324f8ff | trade_date_block_shuffle | 11097 | BLOCKED | False | True | surrun_3be6dd1b710bea7ca7ae58d6 | UNDERPOWERED |
| sspec_49c83645a3956da01324f8ff | trade_date_block_shuffle | 11098 | BLOCKED | False | True | surrun_1c4f18328f20e75734d4de1e | UNDERPOWERED |
| sspec_49c83645a3956da01324f8ff | trade_date_block_shuffle | 11099 | BLOCKED | False | True | surrun_2f863e8d5f420a531e8c793e | UNDERPOWERED |
| sspec_4fe869acc6387192ce021e03 | trade_date_block_shuffle | 11100 | BLOCKED | False | True | surrun_f7108e0ff0cdd9f9daafbce1 | UNDERPOWERED |
| sspec_4fe869acc6387192ce021e03 | trade_date_block_shuffle | 11101 | BLOCKED | False | True | surrun_edbac0e49441b29d44467cf7 | UNDERPOWERED |
| sspec_4fe869acc6387192ce021e03 | trade_date_block_shuffle | 11102 | BLOCKED | False | True | surrun_212dc74cc0ffc71c6215c2e2 | UNDERPOWERED |
| sspec_e5f39f8bb5a751cd64f3452a | trade_date_block_shuffle | 11103 | BLOCKED | False | True | surrun_67b69e184dfb99a7d5668308 | UNDERPOWERED |
| sspec_e5f39f8bb5a751cd64f3452a | trade_date_block_shuffle | 11104 | BLOCKED | False | True | surrun_a540de7846ccd24812b0958c | UNDERPOWERED |
| sspec_e5f39f8bb5a751cd64f3452a | trade_date_block_shuffle | 11105 | BLOCKED | False | True | surrun_66c1b833fd4203b2f3b26b4d | UNDERPOWERED |
| sspec_bcb5b81c7b30afbc3c7d9494 | trade_date_block_shuffle | 11106 | BLOCKED | False | True | surrun_28da8bcd47a4bfe67ef55d60 | UNDERPOWERED |
| sspec_bcb5b81c7b30afbc3c7d9494 | trade_date_block_shuffle | 11107 | BLOCKED | False | True | surrun_585b2c4eb9a8a582f313bdb0 | UNDERPOWERED |
| sspec_bcb5b81c7b30afbc3c7d9494 | trade_date_block_shuffle | 11108 | BLOCKED | False | True | surrun_151ca10dba1ecf30be355d36 | UNDERPOWERED |
| sspec_816c3db399d5b746ca40a8c6 | trade_date_block_shuffle | 11109 | BLOCKED | False | True | surrun_f2890386b7dad7675d889c1c | UNDERPOWERED |
| sspec_816c3db399d5b746ca40a8c6 | trade_date_block_shuffle | 11110 | BLOCKED | False | True | surrun_5a2ddaf0febedff56523e70a | UNDERPOWERED |
| sspec_816c3db399d5b746ca40a8c6 | trade_date_block_shuffle | 11111 | BLOCKED | False | True | surrun_94a9d76f3b8178f2f1b8988e | UNDERPOWERED |
| sspec_f0b31ad6cc243c23a11cbc42 | trade_date_block_shuffle | 11112 | BLOCKED | False | True | surrun_f36a59ab8ad4e6184f8d428f | UNDERPOWERED |
| sspec_f0b31ad6cc243c23a11cbc42 | trade_date_block_shuffle | 11113 | BLOCKED | False | True | surrun_7ed739de390807607b813782 | UNDERPOWERED |
| sspec_f0b31ad6cc243c23a11cbc42 | trade_date_block_shuffle | 11114 | BLOCKED | False | True | surrun_3bcb143823ba2e1df1d7fff9 | UNDERPOWERED |
| sspec_d851a40faead0b037d510433 | trade_date_block_shuffle | 11115 | BLOCKED | False | True | surrun_ae842b6022695e80897eb8a7 | UNDERPOWERED |
| sspec_d851a40faead0b037d510433 | trade_date_block_shuffle | 11116 | BLOCKED | False | True | surrun_80ec10dd3fd441f1c1e91022 | UNDERPOWERED |
| sspec_d851a40faead0b037d510433 | trade_date_block_shuffle | 11117 | BLOCKED | False | True | surrun_2226bf3cf2bd554011f0bb3a | UNDERPOWERED |
| sspec_78b41e38fc5036974930dc2b | trade_date_block_shuffle | 11118 | BLOCKED | False | True | surrun_adaf75f10cea52318d76d47e | UNDERPOWERED |
| sspec_78b41e38fc5036974930dc2b | trade_date_block_shuffle | 11119 | BLOCKED | False | True | surrun_73c174f5e4e01e011d11d7a6 | UNDERPOWERED |
| sspec_78b41e38fc5036974930dc2b | trade_date_block_shuffle | 11120 | BLOCKED | False | True | surrun_c34cab345c8744a4c77c0f3f | UNDERPOWERED |
| sspec_b180e11d1e420660f86a02e0 | trade_date_block_shuffle | 11127 | BLOCKED | False | True | surrun_136fe256e0e2637631c0e265 | UNDERPOWERED |
| sspec_b180e11d1e420660f86a02e0 | trade_date_block_shuffle | 11128 | BLOCKED | False | True | surrun_a387417d3a78016c09c8cf2d | UNDERPOWERED |
| sspec_b180e11d1e420660f86a02e0 | trade_date_block_shuffle | 11129 | BLOCKED | False | True | surrun_8c8f4187416806b35474a6df | UNDERPOWERED |
| sspec_aa37fa251597924ba486e04e | trade_date_block_shuffle | 11130 | BLOCKED | False | True | surrun_297e88e6fbf468c19bf2b4f6 | UNDERPOWERED |
| sspec_aa37fa251597924ba486e04e | trade_date_block_shuffle | 11131 | BLOCKED | False | True | surrun_c234e70ba82b0dc086c4e2ff | UNDERPOWERED |
| sspec_aa37fa251597924ba486e04e | trade_date_block_shuffle | 11132 | BLOCKED | False | True | surrun_989ff51296090ef500cf5225 | UNDERPOWERED |
| sspec_3103fd302018136f473f59ad | trade_date_block_shuffle | 11133 | BLOCKED | False | True | surrun_130113bffcdb08f97734ff28 | UNDERPOWERED |
| sspec_3103fd302018136f473f59ad | trade_date_block_shuffle | 11134 | BLOCKED | False | True | surrun_32110cc33fbcf987c0816651 | UNDERPOWERED |
| sspec_3103fd302018136f473f59ad | trade_date_block_shuffle | 11135 | BLOCKED | False | True | surrun_b480dd7f481454444c9687ac | UNDERPOWERED |
| sspec_5a1e6a6e03fbef7f18ad205b | trade_date_block_shuffle | 11136 | BLOCKED | False | True | surrun_1aa4e174ae3fbf146e16664e | UNDERPOWERED |
| sspec_5a1e6a6e03fbef7f18ad205b | trade_date_block_shuffle | 11137 | BLOCKED | False | True | surrun_e136a25429d65ac442dc5fe4 | UNDERPOWERED |
| sspec_5a1e6a6e03fbef7f18ad205b | trade_date_block_shuffle | 11138 | BLOCKED | False | True | surrun_0c8a53637faec0eaad79b2be | UNDERPOWERED |
| sspec_35010b26e525233351b67050 | trade_date_block_shuffle | 11139 | BLOCKED | False | True | surrun_6fce9f91dc35d76ce94028c2 | UNDERPOWERED |
| sspec_35010b26e525233351b67050 | trade_date_block_shuffle | 11140 | BLOCKED | False | True | surrun_5ca7fe86bc869b10ed2637f7 | UNDERPOWERED |
| sspec_35010b26e525233351b67050 | trade_date_block_shuffle | 11141 | BLOCKED | False | True | surrun_68362efffe7e418ff4703bf7 | UNDERPOWERED |
| sspec_5337203aed1e7a74937ffda8 | trade_date_block_shuffle | 11142 | BLOCKED | False | True | surrun_9bdb961b36aa2b337851d0c7 | UNDERPOWERED |
| sspec_5337203aed1e7a74937ffda8 | trade_date_block_shuffle | 11143 | BLOCKED | False | True | surrun_d6d0f9fa6bd62a79d136d4f7 | UNDERPOWERED |
| sspec_5337203aed1e7a74937ffda8 | trade_date_block_shuffle | 11144 | BLOCKED | False | True | surrun_7ed7c7f3f6d1d22e10842a49 | UNDERPOWERED |
| sspec_6686b645b2967f4de3521142 | trade_date_block_shuffle | 11157 | BLOCKED | False | True | surrun_243aaa9f053327dae524c0fc | UNDERPOWERED |
| sspec_6686b645b2967f4de3521142 | trade_date_block_shuffle | 11158 | BLOCKED | False | True | surrun_ef5415b91e89a71554b8e59a | UNDERPOWERED |
| sspec_6686b645b2967f4de3521142 | trade_date_block_shuffle | 11159 | BLOCKED | False | True | surrun_22bf5134220a9d8680baf828 | UNDERPOWERED |
| sspec_8feca5b9413440472622c188 | trade_date_block_shuffle | 11160 | BLOCKED | False | True | surrun_f6aed260c64794f219bca9ab | UNDERPOWERED |
| sspec_8feca5b9413440472622c188 | trade_date_block_shuffle | 11161 | BLOCKED | False | True | surrun_d07699430c851a424e66f154 | UNDERPOWERED |
| sspec_8feca5b9413440472622c188 | trade_date_block_shuffle | 11162 | BLOCKED | False | True | surrun_c7dda5b2245085161abd8c43 | UNDERPOWERED |
| sspec_3e2b72e4787812cc88d2c3ed | trade_date_block_shuffle | 11163 | BLOCKED | False | True | surrun_6746c9b22d03b0b679bc855b | UNDERPOWERED |
| sspec_3e2b72e4787812cc88d2c3ed | trade_date_block_shuffle | 11164 | BLOCKED | False | True | surrun_3a44dfc523d7a67900c3dc70 | UNDERPOWERED |
| sspec_3e2b72e4787812cc88d2c3ed | trade_date_block_shuffle | 11165 | BLOCKED | False | True | surrun_df5ebf09865cb5aeb1ad0422 | UNDERPOWERED |
| sspec_1740cf32998cef05c858b97f | trade_date_block_shuffle | 11166 | BLOCKED | False | True | surrun_8a291a596e3c52a739266831 | UNDERPOWERED |
| sspec_1740cf32998cef05c858b97f | trade_date_block_shuffle | 11167 | BLOCKED | False | True | surrun_17b3b77137d0dbf925b0b83c | UNDERPOWERED |
| sspec_1740cf32998cef05c858b97f | trade_date_block_shuffle | 11168 | BLOCKED | False | True | surrun_233f348586a49cb8856b97c7 | UNDERPOWERED |
| sspec_14a33e7df4ef804e3016fcfd | trade_date_block_shuffle | 11169 | BLOCKED | False | True | surrun_60666499ca002d0ddd365b36 | UNDERPOWERED |
| sspec_14a33e7df4ef804e3016fcfd | trade_date_block_shuffle | 11170 | BLOCKED | False | True | surrun_c7b03caa042fba79c7ac3bf8 | UNDERPOWERED |
| sspec_14a33e7df4ef804e3016fcfd | trade_date_block_shuffle | 11171 | BLOCKED | False | True | surrun_9428efd86650d9d97ac41748 | UNDERPOWERED |
| sspec_428bd725758c549af88ecb4b | trade_date_block_shuffle | 11172 | BLOCKED | False | True | surrun_3e529306956adc58787b1630 | UNDERPOWERED |
| sspec_428bd725758c549af88ecb4b | trade_date_block_shuffle | 11173 | BLOCKED | False | True | surrun_fc763cbeaa02cff9be08895f | UNDERPOWERED |
| sspec_428bd725758c549af88ecb4b | trade_date_block_shuffle | 11174 | BLOCKED | False | True | surrun_6ba337ecbf7abeb310d5086f | UNDERPOWERED |
| sspec_0598a6105897d79dca528b63 | trade_date_block_shuffle | 11175 | BLOCKED | False | True | surrun_3fc901aa850fd3dbe1ba808f | UNDERPOWERED |
| sspec_0598a6105897d79dca528b63 | trade_date_block_shuffle | 11176 | BLOCKED | False | True | surrun_906a4c2bc8e6e9cdd0e4f3c1 | UNDERPOWERED |
| sspec_0598a6105897d79dca528b63 | trade_date_block_shuffle | 11177 | BLOCKED | False | True | surrun_13dfef10bc37c89752a3b205 | UNDERPOWERED |
| sspec_aca34e15f8036aada065ceb4 | trade_date_block_shuffle | 11178 | BLOCKED | False | True | surrun_c16b46939c72ebef3ca28d88 | UNDERPOWERED |
| sspec_aca34e15f8036aada065ceb4 | trade_date_block_shuffle | 11179 | BLOCKED | False | True | surrun_253f1413b9b49eed33d64d60 | UNDERPOWERED |
| sspec_aca34e15f8036aada065ceb4 | trade_date_block_shuffle | 11180 | BLOCKED | False | True | surrun_6fc470a9e4771948d8f22c90 | UNDERPOWERED |
| sspec_61df4eeee7c7a28e77b295e3 | trade_date_block_shuffle | 11181 | BLOCKED | False | True | surrun_d74459c82bf5a840277af876 | UNDERPOWERED |
| sspec_61df4eeee7c7a28e77b295e3 | trade_date_block_shuffle | 11182 | BLOCKED | False | True | surrun_cf49f19f1255505c9e42b9bd | UNDERPOWERED |
| sspec_61df4eeee7c7a28e77b295e3 | trade_date_block_shuffle | 11183 | BLOCKED | False | True | surrun_130a86e2079e16e28e4c6120 | UNDERPOWERED |
| sspec_550bf30a5885a3fc12028e36 | trade_date_block_shuffle | 11187 | BLOCKED | False | True | surrun_72483f778ec1178ef7581e35 | UNDERPOWERED |
| sspec_550bf30a5885a3fc12028e36 | trade_date_block_shuffle | 11188 | BLOCKED | False | True | surrun_5980da8dcbd00e2e0106ebb2 | UNDERPOWERED |
| sspec_550bf30a5885a3fc12028e36 | trade_date_block_shuffle | 11189 | BLOCKED | False | True | surrun_51e21ffedc0f01c0a9559e3e | UNDERPOWERED |
| sspec_49351d952c375e7a2f88303d | trade_date_block_shuffle | 11190 | BLOCKED | False | True | surrun_87ce735f1b5c652b00254888 | UNDERPOWERED |
| sspec_49351d952c375e7a2f88303d | trade_date_block_shuffle | 11191 | BLOCKED | False | True | surrun_941000f12c1e291c08670215 | UNDERPOWERED |
| sspec_49351d952c375e7a2f88303d | trade_date_block_shuffle | 11192 | BLOCKED | False | True | surrun_cc554477e9451fab269d9100 | UNDERPOWERED |
| sspec_fb980ba3ffcf6d4f5495ea0b | trade_date_block_shuffle | 11193 | BLOCKED | False | True | surrun_b8ac56a647218b95ae9f1e2f | UNDERPOWERED |
| sspec_fb980ba3ffcf6d4f5495ea0b | trade_date_block_shuffle | 11194 | BLOCKED | False | True | surrun_ca7e6d45ee70a6864de8f317 | UNDERPOWERED |
| sspec_fb980ba3ffcf6d4f5495ea0b | trade_date_block_shuffle | 11195 | BLOCKED | False | True | surrun_45dc46d08c9d40326b12dd7b | UNDERPOWERED |
| sspec_22c1ae4e27e920d5fc0aedd1 | trade_date_block_shuffle | 11196 | BLOCKED | False | True | surrun_dc6b65537918f6b12f15e8fc | UNDERPOWERED |
| sspec_22c1ae4e27e920d5fc0aedd1 | trade_date_block_shuffle | 11197 | BLOCKED | False | True | surrun_76db1d8c14ab9ff0aae09521 | UNDERPOWERED |
| sspec_22c1ae4e27e920d5fc0aedd1 | trade_date_block_shuffle | 11198 | BLOCKED | False | True | surrun_419f129e2411be77cec2505d | UNDERPOWERED |
| sspec_0b74115585bdeef812d6570f | trade_date_block_shuffle | 11199 | BLOCKED | False | True | surrun_98d079c5ae8dc9156150445a | UNDERPOWERED |
| sspec_0b74115585bdeef812d6570f | trade_date_block_shuffle | 11200 | BLOCKED | False | True | surrun_8e7045aea722f12210db55e2 | UNDERPOWERED |
| sspec_0b74115585bdeef812d6570f | trade_date_block_shuffle | 11201 | BLOCKED | False | True | surrun_a2369622e6f6c9871d306bb7 | UNDERPOWERED |
| sspec_9cf519546f2d649906291e5b | trade_date_block_shuffle | 11202 | BLOCKED | False | True | surrun_8e33157c8db48e98cbee5383 | UNDERPOWERED |
| sspec_9cf519546f2d649906291e5b | trade_date_block_shuffle | 11203 | BLOCKED | False | True | surrun_f6d57b6bb5c8a0deb8e64950 | UNDERPOWERED |
| sspec_9cf519546f2d649906291e5b | trade_date_block_shuffle | 11204 | BLOCKED | False | True | surrun_7eb0c0277a66b6efa4e12eb1 | UNDERPOWERED |
| sspec_16dbaeb5cc9f96b689f3651e | trade_date_block_shuffle | 11205 | BLOCKED | False | True | surrun_bda55d495949e6ca2a370cd1 | UNDERPOWERED |
| sspec_16dbaeb5cc9f96b689f3651e | trade_date_block_shuffle | 11206 | BLOCKED | False | True | surrun_5b0d00d1e077b81a5df50063 | UNDERPOWERED |
| sspec_16dbaeb5cc9f96b689f3651e | trade_date_block_shuffle | 11207 | BLOCKED | False | True | surrun_e5cdafc71e0944203820a148 | UNDERPOWERED |
| sspec_adce3f052100b7b14fc97ff9 | trade_date_block_shuffle | 11208 | BLOCKED | False | True | surrun_2a414ca6fc2fe7e3f3f6a96c | UNDERPOWERED |
| sspec_adce3f052100b7b14fc97ff9 | trade_date_block_shuffle | 11209 | BLOCKED | False | True | surrun_d4724ea45cd9a1051a51c322 | UNDERPOWERED |
| sspec_adce3f052100b7b14fc97ff9 | trade_date_block_shuffle | 11210 | BLOCKED | False | True | surrun_e91979999387bbc78086b3c2 | UNDERPOWERED |
| sspec_d57bd0277f061a202fe1884e | trade_date_block_shuffle | 11217 | BLOCKED | False | True | surrun_ba3fed28440d993aae4d7712 | UNDERPOWERED |
| sspec_d57bd0277f061a202fe1884e | trade_date_block_shuffle | 11218 | BLOCKED | False | True | surrun_0564ba06a037518016b83c89 | UNDERPOWERED |
| sspec_d57bd0277f061a202fe1884e | trade_date_block_shuffle | 11219 | BLOCKED | False | True | surrun_0966171d40389c716996adad | UNDERPOWERED |
| sspec_4fa746784450d2c524017fa4 | trade_date_block_bootstrap | 11220 | BLOCKED | False | True | surrun_b46cb919e0ea8d179745c4fa | UNDERPOWERED |
| sspec_4fa746784450d2c524017fa4 | trade_date_block_bootstrap | 11221 | BLOCKED | False | True | surrun_8eb980240ed3e9f5120a8cc3 | UNDERPOWERED |
| sspec_4fa746784450d2c524017fa4 | trade_date_block_bootstrap | 11222 | BLOCKED | False | True | surrun_16c1a9564f72ad4b2eb0b9af | UNDERPOWERED |
| sspec_1c57243ef0c7c60974874414 | trade_date_block_bootstrap | 11223 | BLOCKED | False | False | surrun_89001e151126a5a8187b5b1a | UNDERPOWERED |
| sspec_1c57243ef0c7c60974874414 | trade_date_block_bootstrap | 11224 | BLOCKED | False | False | surrun_466660d02eb78476cedbae63 | UNDERPOWERED |
| sspec_1c57243ef0c7c60974874414 | trade_date_block_bootstrap | 11225 | BLOCKED | False | False | surrun_e57fd707c7628adc8d889021 | UNDERPOWERED |
| sspec_319a2690890476bc88427bf4 | trade_date_block_bootstrap | 11226 | BLOCKED | False | True | surrun_4c9214d1ce9755ebb2d1cace | UNDERPOWERED |
| sspec_319a2690890476bc88427bf4 | trade_date_block_bootstrap | 11227 | BLOCKED | False | True | surrun_da622dbf147dc87fb2aef172 | UNDERPOWERED |
| sspec_319a2690890476bc88427bf4 | trade_date_block_bootstrap | 11228 | BLOCKED | False | True | surrun_62ae108afed7234e571d8bdb | UNDERPOWERED |
| sspec_5c5c2c5889d9efe89bd8b5ef | trade_date_block_bootstrap | 11229 | BLOCKED | False | True | surrun_8df5b7d72f733a946021d6f6 | UNDERPOWERED |
| sspec_5c5c2c5889d9efe89bd8b5ef | trade_date_block_bootstrap | 11230 | BLOCKED | False | True | surrun_526328123b816608fdb69024 | UNDERPOWERED |
| sspec_5c5c2c5889d9efe89bd8b5ef | trade_date_block_bootstrap | 11231 | BLOCKED | False | True | surrun_7a9c7e3931066686124e266c | UNDERPOWERED |
| sspec_ea87025ac137123d3fdb2c93 | trade_date_block_bootstrap | 11232 | BLOCKED | False | True | surrun_128d7307ae929e1a6456d3b7 | UNDERPOWERED |
| sspec_ea87025ac137123d3fdb2c93 | trade_date_block_bootstrap | 11233 | BLOCKED | False | True | surrun_e0706a0321c4235bafd292cb | UNDERPOWERED |
| sspec_ea87025ac137123d3fdb2c93 | trade_date_block_bootstrap | 11234 | BLOCKED | False | True | surrun_0c622ef2595cf3f34d1a324c | UNDERPOWERED |
| sspec_00839ae5b9943f831d39227b | trade_date_block_bootstrap | 11247 | BLOCKED | False | True | surrun_08ba195849e8dfca9dee065c | UNDERPOWERED |
| sspec_00839ae5b9943f831d39227b | trade_date_block_bootstrap | 11248 | BLOCKED | False | True | surrun_46628e8841152a1c8d2779a3 | UNDERPOWERED |
| sspec_00839ae5b9943f831d39227b | trade_date_block_bootstrap | 11249 | BLOCKED | False | True | surrun_d33b2d72f69c0bbe06a44e5f | UNDERPOWERED |
| sspec_e564d69e4a8ef7e527b12504 | trade_date_block_bootstrap | 11250 | BLOCKED | False | True | surrun_3d745d0493ca411257e093a5 | UNDERPOWERED |
| sspec_e564d69e4a8ef7e527b12504 | trade_date_block_bootstrap | 11251 | BLOCKED | False | True | surrun_bcd17792a1abe4781ca836e3 | UNDERPOWERED |
| sspec_e564d69e4a8ef7e527b12504 | trade_date_block_bootstrap | 11252 | BLOCKED | False | True | surrun_9a96493d7092dc3d44f599e6 | UNDERPOWERED |
| sspec_acb32ca61cf5a0db09f9de1e | trade_date_block_bootstrap | 11253 | BLOCKED | False | False | surrun_8e7ecad92f8ac9d7ce26f142 | UNDERPOWERED |
| sspec_acb32ca61cf5a0db09f9de1e | trade_date_block_bootstrap | 11254 | BLOCKED | False | False | surrun_455f3220806a3abbfb753273 | UNDERPOWERED |
| sspec_acb32ca61cf5a0db09f9de1e | trade_date_block_bootstrap | 11255 | BLOCKED | False | False | surrun_675fb829954f4307235db786 | UNDERPOWERED |
| sspec_944e13f0744afe9fdd238171 | trade_date_block_bootstrap | 11256 | BLOCKED | False | True | surrun_c8dded9444c0877e3d2b1a48 | UNDERPOWERED |
| sspec_944e13f0744afe9fdd238171 | trade_date_block_bootstrap | 11257 | BLOCKED | False | True | surrun_76c612cc52d48899dacdef8f | UNDERPOWERED |
| sspec_944e13f0744afe9fdd238171 | trade_date_block_bootstrap | 11258 | BLOCKED | False | True | surrun_e9ca39ef68a93638f97f959a | UNDERPOWERED |
| sspec_89dd5997cfe81a14b68e1f7c | trade_date_block_bootstrap | 11259 | BLOCKED | False | True | surrun_1ac2f9ebb65fd9f539fda082 | UNDERPOWERED |
| sspec_89dd5997cfe81a14b68e1f7c | trade_date_block_bootstrap | 11260 | BLOCKED | False | True | surrun_972219e8ce3d667713432a1b | UNDERPOWERED |
| sspec_89dd5997cfe81a14b68e1f7c | trade_date_block_bootstrap | 11261 | BLOCKED | False | True | surrun_a4f96b2dfd47f7126e41034e | UNDERPOWERED |
| sspec_36204b43ca6b58dbb7701c08 | trade_date_block_bootstrap | 11262 | BLOCKED | False | True | surrun_c7836939302902aabb8ecbc6 | UNDERPOWERED |
| sspec_36204b43ca6b58dbb7701c08 | trade_date_block_bootstrap | 11263 | BLOCKED | False | True | surrun_a9646ab596f8344827239402 | UNDERPOWERED |
| sspec_36204b43ca6b58dbb7701c08 | trade_date_block_bootstrap | 11264 | BLOCKED | False | True | surrun_2340ef937dfa202d9acd170f | UNDERPOWERED |
| sspec_36a36f0485335d18313d8e0e | trade_date_block_bootstrap | 11265 | BLOCKED | False | True | surrun_6f43c9912d9d1009faac0643 | UNDERPOWERED |
| sspec_36a36f0485335d18313d8e0e | trade_date_block_bootstrap | 11266 | BLOCKED | False | True | surrun_4df78d2b2aa4c08a63bad8cd | UNDERPOWERED |
| sspec_36a36f0485335d18313d8e0e | trade_date_block_bootstrap | 11267 | BLOCKED | False | True | surrun_49d77fe103fdf87afbd1e9bc | UNDERPOWERED |
| sspec_0ebc6d34934a8aedee7471a8 | trade_date_block_bootstrap | 11268 | BLOCKED | False | True | surrun_c53c850ede3e235eb81bb660 | UNDERPOWERED |
| sspec_0ebc6d34934a8aedee7471a8 | trade_date_block_bootstrap | 11269 | BLOCKED | False | True | surrun_37e8a0b991ba6c6409f3dccc | UNDERPOWERED |
| sspec_0ebc6d34934a8aedee7471a8 | trade_date_block_bootstrap | 11270 | BLOCKED | False | True | surrun_ab178a71a7a924f5c4a1a68f | UNDERPOWERED |
| sspec_55eb525b1eee4eff7cac1bdf | trade_date_block_bootstrap | 11271 | BLOCKED | False | True | surrun_48748d332b7e03f49989dcb3 | UNDERPOWERED |
| sspec_55eb525b1eee4eff7cac1bdf | trade_date_block_bootstrap | 11272 | BLOCKED | False | True | surrun_26cf8db2fb4aa08765e20811 | UNDERPOWERED |
| sspec_55eb525b1eee4eff7cac1bdf | trade_date_block_bootstrap | 11273 | BLOCKED | False | True | surrun_bcf3a406a51f6f6f71955f5e | UNDERPOWERED |
| sspec_72b4c4fa564ff882a84d22ca | trade_date_block_bootstrap | 11277 | BLOCKED | False | True | surrun_a0dc105f6251bffbdc6a4127 | UNDERPOWERED |
| sspec_72b4c4fa564ff882a84d22ca | trade_date_block_bootstrap | 11278 | BLOCKED | False | True | surrun_bdd52199e96ae373db8db978 | UNDERPOWERED |
| sspec_72b4c4fa564ff882a84d22ca | trade_date_block_bootstrap | 11279 | BLOCKED | False | True | surrun_199abff28d40b028bfdf7b3b | UNDERPOWERED |
| sspec_a39a5a070a5625740fae6601 | trade_date_block_bootstrap | 11280 | BLOCKED | False | True | surrun_5272cccd2e61e1776533f86b | UNDERPOWERED |
| sspec_a39a5a070a5625740fae6601 | trade_date_block_bootstrap | 11281 | BLOCKED | False | True | surrun_bb0a04a97a12e307e5edda82 | UNDERPOWERED |
| sspec_a39a5a070a5625740fae6601 | trade_date_block_bootstrap | 11282 | BLOCKED | False | True | surrun_44895a970a990013330621bd | UNDERPOWERED |
| sspec_3ddbe3eced9b9facefc9d426 | trade_date_block_bootstrap | 11283 | BLOCKED | False | False | surrun_0b8f8ab57caf2ea6761edcef | UNDERPOWERED |
| sspec_3ddbe3eced9b9facefc9d426 | trade_date_block_bootstrap | 11284 | BLOCKED | False | False | surrun_27a6822a29cfa04ab2d76ec3 | UNDERPOWERED |
| sspec_3ddbe3eced9b9facefc9d426 | trade_date_block_bootstrap | 11285 | BLOCKED | False | False | surrun_b3d97c088911ba37605fdbec | UNDERPOWERED |
| sspec_173b965245816178171ff8ef | trade_date_block_bootstrap | 11286 | BLOCKED | False | True | surrun_261e2554021f3d8ea06bcfef | UNDERPOWERED |
| sspec_173b965245816178171ff8ef | trade_date_block_bootstrap | 11287 | BLOCKED | False | True | surrun_4d2214419f07cb11a4038bdf | UNDERPOWERED |
| sspec_173b965245816178171ff8ef | trade_date_block_bootstrap | 11288 | BLOCKED | False | True | surrun_3769fc77a16949022e90cf01 | UNDERPOWERED |
| sspec_b00754db8caafd5990665ab9 | trade_date_block_bootstrap | 11289 | BLOCKED | False | True | surrun_16baae92998e24027fccdf66 | UNDERPOWERED |
| sspec_b00754db8caafd5990665ab9 | trade_date_block_bootstrap | 11290 | BLOCKED | False | True | surrun_e5576e3130f1b9f4d40a50b8 | UNDERPOWERED |
| sspec_b00754db8caafd5990665ab9 | trade_date_block_bootstrap | 11291 | BLOCKED | False | True | surrun_6c46a6e82e8d746b142196df | UNDERPOWERED |
| sspec_77f49aefe2063edf9fcd9fe6 | trade_date_block_bootstrap | 11292 | BLOCKED | False | True | surrun_c77d16c7b928c66158e8c401 | UNDERPOWERED |
| sspec_77f49aefe2063edf9fcd9fe6 | trade_date_block_bootstrap | 11293 | BLOCKED | False | True | surrun_e9585dd785a9455c780bb192 | UNDERPOWERED |
| sspec_77f49aefe2063edf9fcd9fe6 | trade_date_block_bootstrap | 11294 | BLOCKED | False | True | surrun_6a37123300bf506fe5bd12cb | UNDERPOWERED |
| sspec_a6516a8847202e7da75ad5cb | trade_date_block_bootstrap | 11295 | BLOCKED | False | True | surrun_c289299ba02892baa5131353 | UNDERPOWERED |
| sspec_a6516a8847202e7da75ad5cb | trade_date_block_bootstrap | 11296 | BLOCKED | False | True | surrun_384181b64ca2fd34f5fffb29 | UNDERPOWERED |
| sspec_a6516a8847202e7da75ad5cb | trade_date_block_bootstrap | 11297 | BLOCKED | False | True | surrun_d45b125435f8640f0e96fce7 | UNDERPOWERED |
| sspec_c5e1b38c31b506856a875ef3 | trade_date_block_bootstrap | 11298 | BLOCKED | False | True | surrun_3671c9e9bf6221d55d0c633d | UNDERPOWERED |
| sspec_c5e1b38c31b506856a875ef3 | trade_date_block_bootstrap | 11299 | BLOCKED | False | True | surrun_d8e752c3e0945e81d98c1ec1 | UNDERPOWERED |
| sspec_c5e1b38c31b506856a875ef3 | trade_date_block_bootstrap | 11300 | BLOCKED | False | True | surrun_2be34c74b384a7c8a9756a71 | UNDERPOWERED |
| sspec_573fbf60517c40db277e1f0f | trade_date_block_bootstrap | 11307 | BLOCKED | False | True | surrun_72fac85ba2f17c81561a2ba2 | UNDERPOWERED |
| sspec_573fbf60517c40db277e1f0f | trade_date_block_bootstrap | 11308 | BLOCKED | False | True | surrun_8623d1d474ac623a967d73dc | UNDERPOWERED |
| sspec_573fbf60517c40db277e1f0f | trade_date_block_bootstrap | 11309 | BLOCKED | False | True | surrun_8b050ff79d972f6b03c176fa | UNDERPOWERED |
| sspec_0da1b86bd637df69b484dc17 | trade_date_block_bootstrap | 11310 | BLOCKED | False | True | surrun_71d0f9cef52f5b458240b6b4 | UNDERPOWERED |
| sspec_0da1b86bd637df69b484dc17 | trade_date_block_bootstrap | 11311 | BLOCKED | False | True | surrun_5232118ec7118fe8340d2254 | UNDERPOWERED |
| sspec_0da1b86bd637df69b484dc17 | trade_date_block_bootstrap | 11312 | BLOCKED | False | True | surrun_3589f886fbd831bc63caef50 | UNDERPOWERED |
| sspec_ac9de244fbb515f2fa22615d | trade_date_block_bootstrap | 11313 | BLOCKED | False | False | surrun_5dd809ee6a7c89ad591e836c | UNDERPOWERED |
| sspec_ac9de244fbb515f2fa22615d | trade_date_block_bootstrap | 11314 | BLOCKED | False | False | surrun_f948eef711c7621fdf13ee43 | UNDERPOWERED |
| sspec_ac9de244fbb515f2fa22615d | trade_date_block_bootstrap | 11315 | BLOCKED | False | False | surrun_30a095ccc6255d91fa73affa | UNDERPOWERED |
| sspec_3f391da448f5d99814a7e9db | trade_date_block_bootstrap | 11316 | BLOCKED | False | True | surrun_fbff4651dfdbbdc07c768736 | UNDERPOWERED |
| sspec_3f391da448f5d99814a7e9db | trade_date_block_bootstrap | 11317 | BLOCKED | False | True | surrun_7bf06688e2868786b1ca6b94 | UNDERPOWERED |
| sspec_3f391da448f5d99814a7e9db | trade_date_block_bootstrap | 11318 | BLOCKED | False | True | surrun_d5fc1c6da6ec5f6d70918bf2 | UNDERPOWERED |
| sspec_b9385c7ac215e605906f6d6e | trade_date_block_bootstrap | 11319 | BLOCKED | False | True | surrun_315710b50df26b4965e0e99a | UNDERPOWERED |
| sspec_b9385c7ac215e605906f6d6e | trade_date_block_bootstrap | 11320 | BLOCKED | False | True | surrun_e09c256b769b209ed77fa1e0 | UNDERPOWERED |
| sspec_b9385c7ac215e605906f6d6e | trade_date_block_bootstrap | 11321 | BLOCKED | False | True | surrun_88944d56dfbf22d5e01710e7 | UNDERPOWERED |
| sspec_470f031a3b85a887bad9f587 | trade_date_block_bootstrap | 11322 | BLOCKED | False | True | surrun_afcd7a74c7ad82c4d3a40c59 | UNDERPOWERED |
| sspec_470f031a3b85a887bad9f587 | trade_date_block_bootstrap | 11323 | BLOCKED | False | True | surrun_717064061d53abd83d912bd0 | UNDERPOWERED |
| sspec_470f031a3b85a887bad9f587 | trade_date_block_bootstrap | 11324 | BLOCKED | False | True | surrun_67b3ec66c37a17c56292f536 | UNDERPOWERED |
| sspec_52095f4e99ebe557b96d4639 | trade_date_block_bootstrap | 11325 | BLOCKED | False | True | surrun_23fa0f042445fe5c3fd254ea | UNDERPOWERED |
| sspec_52095f4e99ebe557b96d4639 | trade_date_block_bootstrap | 11326 | BLOCKED | False | True | surrun_f6eafea368575859193efea9 | UNDERPOWERED |
| sspec_52095f4e99ebe557b96d4639 | trade_date_block_bootstrap | 11327 | BLOCKED | False | True | surrun_4ea871a593bbdf68059b9773 | UNDERPOWERED |
| sspec_40eddd44e9e5dee029c1d699 | trade_date_block_bootstrap | 11328 | BLOCKED | False | True | surrun_b6ebd6e4b1e7d87237f19342 | UNDERPOWERED |
| sspec_40eddd44e9e5dee029c1d699 | trade_date_block_bootstrap | 11329 | BLOCKED | False | True | surrun_05884a984b51493effc65204 | UNDERPOWERED |
| sspec_40eddd44e9e5dee029c1d699 | trade_date_block_bootstrap | 11330 | BLOCKED | False | True | surrun_bd7c5b863c809920e684370e | UNDERPOWERED |
| sspec_af34dfb90556059712d9deb2 | trade_date_block_bootstrap | 11331 | BLOCKED | False | True | surrun_1a9a3d0071b7022674169d73 | UNDERPOWERED |
| sspec_af34dfb90556059712d9deb2 | trade_date_block_bootstrap | 11332 | BLOCKED | False | True | surrun_7a4480af0c7688fc1f406daa | UNDERPOWERED |
| sspec_af34dfb90556059712d9deb2 | trade_date_block_bootstrap | 11333 | BLOCKED | False | True | surrun_b22c5f32d0e6dd90076e5347 | UNDERPOWERED |
| sspec_6cbd4448bb637b57a5798941 | trade_date_block_bootstrap | 11337 | BLOCKED | False | True | surrun_5d6d3d98f5faacc2a4260959 | UNDERPOWERED |
| sspec_6cbd4448bb637b57a5798941 | trade_date_block_bootstrap | 11338 | BLOCKED | False | True | surrun_952e08846abf1b7d68a6eed9 | UNDERPOWERED |
| sspec_6cbd4448bb637b57a5798941 | trade_date_block_bootstrap | 11339 | BLOCKED | False | True | surrun_a2746e7894a54174dec4d1eb | UNDERPOWERED |
| sspec_9db4771cbb0bfd2e1dc16587 | trade_date_block_bootstrap | 11340 | BLOCKED | False | True | surrun_9fdeeccb79ad143a51635d8d | UNDERPOWERED |
| sspec_9db4771cbb0bfd2e1dc16587 | trade_date_block_bootstrap | 11341 | BLOCKED | False | True | surrun_10d2b290465cf489585b73a2 | UNDERPOWERED |
| sspec_9db4771cbb0bfd2e1dc16587 | trade_date_block_bootstrap | 11342 | BLOCKED | False | True | surrun_328ecaa8b2299027662e2c21 | UNDERPOWERED |
| sspec_05b3a4d953a49c77aa1cc5eb | trade_date_block_bootstrap | 11343 | BLOCKED | False | False | surrun_7b5100fb0c06048ee4338f18 | UNDERPOWERED |
| sspec_05b3a4d953a49c77aa1cc5eb | trade_date_block_bootstrap | 11344 | BLOCKED | False | False | surrun_6d9ef5cff697c056f0c8a706 | UNDERPOWERED |
| sspec_05b3a4d953a49c77aa1cc5eb | trade_date_block_bootstrap | 11345 | BLOCKED | False | False | surrun_55600b259d2408d5cde813fa | UNDERPOWERED |
| sspec_a44f6ffdeb0ef3d9fe989c74 | trade_date_block_bootstrap | 11346 | BLOCKED | False | True | surrun_8c19bbf889940d254a7846c5 | UNDERPOWERED |
| sspec_a44f6ffdeb0ef3d9fe989c74 | trade_date_block_bootstrap | 11347 | BLOCKED | False | True | surrun_d9101d0915bfe849cfc85271 | UNDERPOWERED |
| sspec_a44f6ffdeb0ef3d9fe989c74 | trade_date_block_bootstrap | 11348 | BLOCKED | False | True | surrun_5fc66bbb86735eef63d97abd | UNDERPOWERED |
| sspec_73a87c9e9bb8f8abbf71489d | trade_date_block_bootstrap | 11349 | BLOCKED | False | True | surrun_33decf5c5cf67a62ba2ab67c | UNDERPOWERED |
| sspec_73a87c9e9bb8f8abbf71489d | trade_date_block_bootstrap | 11350 | BLOCKED | False | True | surrun_060a2f215c01e307866ee994 | UNDERPOWERED |
| sspec_73a87c9e9bb8f8abbf71489d | trade_date_block_bootstrap | 11351 | BLOCKED | False | True | surrun_a02284c7c659014612e6901a | UNDERPOWERED |
| sspec_2f878cd3fc2024e7ea421e27 | trade_date_block_bootstrap | 11352 | BLOCKED | False | True | surrun_7ab83dfbd17f28feb964baa6 | UNDERPOWERED |
| sspec_2f878cd3fc2024e7ea421e27 | trade_date_block_bootstrap | 11353 | BLOCKED | False | True | surrun_8c85537b6967fd799e331938 | UNDERPOWERED |
| sspec_2f878cd3fc2024e7ea421e27 | trade_date_block_bootstrap | 11354 | BLOCKED | False | True | surrun_1136d50011bec44f15ea92ee | UNDERPOWERED |
| sspec_1f17dbacaeea51d6adc19b62 | trade_date_block_bootstrap | 11355 | BLOCKED | False | True | surrun_8fe431d804c4e34e8b46ed0f | UNDERPOWERED |
| sspec_1f17dbacaeea51d6adc19b62 | trade_date_block_bootstrap | 11356 | BLOCKED | False | True | surrun_fbbd09e71494f62a1e8edd08 | UNDERPOWERED |
| sspec_1f17dbacaeea51d6adc19b62 | trade_date_block_bootstrap | 11357 | BLOCKED | False | True | surrun_72a2e3c52bf4dcfc9a3f0eab | UNDERPOWERED |
| sspec_42b7484aa7400a013c35979e | trade_date_block_bootstrap | 11358 | BLOCKED | False | True | surrun_db6e771fb8b08b9eabd8e84b | UNDERPOWERED |
| sspec_42b7484aa7400a013c35979e | trade_date_block_bootstrap | 11359 | BLOCKED | False | True | surrun_d2e0d84ad19ce603ba357bf8 | UNDERPOWERED |
| sspec_42b7484aa7400a013c35979e | trade_date_block_bootstrap | 11360 | BLOCKED | False | True | surrun_be2126794f62a34e70974ae3 | UNDERPOWERED |
| sspec_83973637948a060c1a01d3ec | trade_date_block_bootstrap | 11367 | BLOCKED | False | True | surrun_db684599aa9529176bfa2337 | UNDERPOWERED |
| sspec_83973637948a060c1a01d3ec | trade_date_block_bootstrap | 11368 | BLOCKED | False | True | surrun_6e4f54591dc0c10aa707b662 | UNDERPOWERED |
| sspec_83973637948a060c1a01d3ec | trade_date_block_bootstrap | 11369 | BLOCKED | False | True | surrun_adaa6c05cc3766725489b060 | UNDERPOWERED |
| sspec_6182442ead006ecd05c0bfc6 | trade_date_block_bootstrap | 11370 | BLOCKED | False | True | surrun_1b5f953c74b86c4238b4b349 | UNDERPOWERED |
| sspec_6182442ead006ecd05c0bfc6 | trade_date_block_bootstrap | 11371 | BLOCKED | False | True | surrun_163382d65dd5501ba8ed87df | UNDERPOWERED |
| sspec_6182442ead006ecd05c0bfc6 | trade_date_block_bootstrap | 11372 | BLOCKED | False | True | surrun_e8b2da68169f9598d582967f | UNDERPOWERED |
| sspec_af22bf758cac2e63e4dc15c0 | trade_date_block_bootstrap | 11373 | BLOCKED | False | False | surrun_f3d98ece449b1c3c531b9599 | UNDERPOWERED |
| sspec_af22bf758cac2e63e4dc15c0 | trade_date_block_bootstrap | 11374 | BLOCKED | False | False | surrun_d25619365b4d2ddb20c1d8a6 | UNDERPOWERED |
| sspec_af22bf758cac2e63e4dc15c0 | trade_date_block_bootstrap | 11375 | BLOCKED | False | False | surrun_8d47f77e9f687b3f00ad5ecd | UNDERPOWERED |
| sspec_bacc76cfa935c22e95cff9c2 | trade_date_block_bootstrap | 11376 | BLOCKED | False | True | surrun_fcda97e7ddc47f4cdfb8cf4b | UNDERPOWERED |
| sspec_bacc76cfa935c22e95cff9c2 | trade_date_block_bootstrap | 11377 | BLOCKED | False | True | surrun_da58c826e295b3b07d98d8c1 | UNDERPOWERED |
| sspec_bacc76cfa935c22e95cff9c2 | trade_date_block_bootstrap | 11378 | BLOCKED | False | True | surrun_63e4e00887e7df566471d06b | UNDERPOWERED |
| sspec_2f7befddef61d91d4f89fd55 | trade_date_block_bootstrap | 11379 | BLOCKED | False | True | surrun_87ca352741362afadabd19c6 | UNDERPOWERED |
| sspec_2f7befddef61d91d4f89fd55 | trade_date_block_bootstrap | 11380 | BLOCKED | False | True | surrun_568c5eaa750a0d6fd6e9b48b | UNDERPOWERED |
| sspec_2f7befddef61d91d4f89fd55 | trade_date_block_bootstrap | 11381 | BLOCKED | False | True | surrun_e99e70527650c17a493ef27f | UNDERPOWERED |
| sspec_01f0aa8d473da54027cde20c | trade_date_block_bootstrap | 11382 | BLOCKED | False | True | surrun_07e6a5d5ee25a973e6f768c4 | UNDERPOWERED |
| sspec_01f0aa8d473da54027cde20c | trade_date_block_bootstrap | 11383 | BLOCKED | False | True | surrun_9610adc4b202e2d14df5ed8c | UNDERPOWERED |
| sspec_01f0aa8d473da54027cde20c | trade_date_block_bootstrap | 11384 | BLOCKED | False | True | surrun_7b375fdc2f83506b31a7e033 | UNDERPOWERED |
| sspec_67ab4b458039125b4bdce718 | trade_date_block_bootstrap | 11385 | BLOCKED | False | True | surrun_2adba3c3a2e2d0301cfd4ad1 | UNDERPOWERED |
| sspec_67ab4b458039125b4bdce718 | trade_date_block_bootstrap | 11386 | BLOCKED | False | True | surrun_2c5cc6de62680eafcd38173d | UNDERPOWERED |
| sspec_67ab4b458039125b4bdce718 | trade_date_block_bootstrap | 11387 | BLOCKED | False | True | surrun_240606867dca23cdd65c0ef0 | UNDERPOWERED |
| sspec_a14c646b8b4c76bcafbfc9eb | trade_date_block_bootstrap | 11388 | BLOCKED | False | True | surrun_7f9bc45322a9273800e9f630 | UNDERPOWERED |
| sspec_a14c646b8b4c76bcafbfc9eb | trade_date_block_bootstrap | 11389 | BLOCKED | False | True | surrun_4d8cfd1905a265c00ae27bd6 | UNDERPOWERED |
| sspec_a14c646b8b4c76bcafbfc9eb | trade_date_block_bootstrap | 11390 | BLOCKED | False | True | surrun_3e242cef8cbf5e59f5f81a00 | UNDERPOWERED |
| sspec_89d14d5cbf1c84899310e61f | trade_date_block_bootstrap | 11397 | BLOCKED | False | True | surrun_b548ff95f0fc3c4783de4ae2 | UNDERPOWERED |
| sspec_89d14d5cbf1c84899310e61f | trade_date_block_bootstrap | 11398 | BLOCKED | False | True | surrun_92ab67be7390e6bbf604d986 | UNDERPOWERED |
| sspec_89d14d5cbf1c84899310e61f | trade_date_block_bootstrap | 11399 | BLOCKED | False | True | surrun_08b5932e965d17bb48152ed2 | UNDERPOWERED |
| sspec_9b066dbd9d80291f1ff74b27 | trade_date_block_bootstrap | 11400 | BLOCKED | False | True | surrun_cecaa99c4146c63a83e85d3a | UNDERPOWERED |
| sspec_9b066dbd9d80291f1ff74b27 | trade_date_block_bootstrap | 11401 | BLOCKED | False | True | surrun_410c083a936cde1508b4d436 | UNDERPOWERED |
| sspec_9b066dbd9d80291f1ff74b27 | trade_date_block_bootstrap | 11402 | BLOCKED | False | True | surrun_74aeffade48e779576125810 | UNDERPOWERED |
| sspec_b88f6a5a7a8dc7236e664b7e | trade_date_block_bootstrap | 11403 | BLOCKED | False | False | surrun_aab8f8de4968f19ad8f2beae | UNDERPOWERED |
| sspec_b88f6a5a7a8dc7236e664b7e | trade_date_block_bootstrap | 11404 | BLOCKED | False | False | surrun_31ae6e789b655a6b5c7120df | UNDERPOWERED |
| sspec_b88f6a5a7a8dc7236e664b7e | trade_date_block_bootstrap | 11405 | BLOCKED | False | False | surrun_5f70ed29857442e57e78213a | UNDERPOWERED |
| sspec_be3a8ed3aefcb6e180f8835b | trade_date_block_bootstrap | 11406 | BLOCKED | False | True | surrun_79be155721cf9ed004a19cf4 | UNDERPOWERED |
| sspec_be3a8ed3aefcb6e180f8835b | trade_date_block_bootstrap | 11407 | BLOCKED | False | True | surrun_769f0e07599146e42ca46dd6 | UNDERPOWERED |
| sspec_be3a8ed3aefcb6e180f8835b | trade_date_block_bootstrap | 11408 | BLOCKED | False | True | surrun_ed1554f77241454ce328ce52 | UNDERPOWERED |
| sspec_dfa123db9ed79da51e68e86a | trade_date_block_bootstrap | 11409 | BLOCKED | False | True | surrun_5c77f1b6d441800b9bb2035b | UNDERPOWERED |
| sspec_dfa123db9ed79da51e68e86a | trade_date_block_bootstrap | 11410 | BLOCKED | False | True | surrun_b28f0cafa29984850679f702 | UNDERPOWERED |
| sspec_dfa123db9ed79da51e68e86a | trade_date_block_bootstrap | 11411 | BLOCKED | False | True | surrun_9f805d25161c3b2324985516 | UNDERPOWERED |
| sspec_4b48ee8f1b16b3c796301091 | trade_date_block_bootstrap | 11412 | BLOCKED | False | True | surrun_49b943f5bcd1f0e62e500481 | UNDERPOWERED |
| sspec_4b48ee8f1b16b3c796301091 | trade_date_block_bootstrap | 11413 | BLOCKED | False | True | surrun_f704b3e4fb80fc359c4cbbcf | UNDERPOWERED |
| sspec_4b48ee8f1b16b3c796301091 | trade_date_block_bootstrap | 11414 | BLOCKED | False | True | surrun_f2526b18d15b028030e96fbd | UNDERPOWERED |
| sspec_8c1f5685bf76f63f1918678f | trade_date_block_bootstrap | 11415 | BLOCKED | False | True | surrun_51a71dfc8c76457faad2c0dc | UNDERPOWERED |
| sspec_8c1f5685bf76f63f1918678f | trade_date_block_bootstrap | 11416 | BLOCKED | False | True | surrun_416b92d6e4d2c72f08cc7458 | UNDERPOWERED |
| sspec_8c1f5685bf76f63f1918678f | trade_date_block_bootstrap | 11417 | BLOCKED | False | True | surrun_45940178ec1f6085a154ea77 | UNDERPOWERED |
| sspec_9466e5812145ed99c77addd8 | trade_date_block_bootstrap | 11418 | BLOCKED | False | True | surrun_e1412f452c8519483edda4b8 | UNDERPOWERED |
| sspec_9466e5812145ed99c77addd8 | trade_date_block_bootstrap | 11419 | BLOCKED | False | True | surrun_0e63ff56948380b8f1dca98a | UNDERPOWERED |
| sspec_9466e5812145ed99c77addd8 | trade_date_block_bootstrap | 11420 | BLOCKED | False | True | surrun_fe30293d40b1a4bdff42b5bd | UNDERPOWERED |
| sspec_3bd847d9c68620974d8e4e58 | trade_date_block_bootstrap | 11427 | BLOCKED | False | True | surrun_28aa6f666c337c25f80f9008 | UNDERPOWERED |
| sspec_3bd847d9c68620974d8e4e58 | trade_date_block_bootstrap | 11428 | BLOCKED | False | True | surrun_8cf281f71d2785d592ad47eb | UNDERPOWERED |
| sspec_3bd847d9c68620974d8e4e58 | trade_date_block_bootstrap | 11429 | BLOCKED | False | True | surrun_73a875cca3ef9b1794713c53 | UNDERPOWERED |
| sspec_86adf765160a896363bcd5b9 | trade_date_block_bootstrap | 11430 | BLOCKED | False | True | surrun_3d1f3edfc54ff7f4797a7da7 | UNDERPOWERED |
| sspec_86adf765160a896363bcd5b9 | trade_date_block_bootstrap | 11431 | BLOCKED | False | True | surrun_34ac995e14a14736f0782bcc | UNDERPOWERED |
| sspec_86adf765160a896363bcd5b9 | trade_date_block_bootstrap | 11432 | BLOCKED | False | True | surrun_da249801a7dffededb6bc158 | UNDERPOWERED |
| sspec_fd2750a3aca045563eb8af6b | trade_date_block_bootstrap | 11433 | BLOCKED | False | False | surrun_c3e07a704c58882792b36243 | UNDERPOWERED |
| sspec_fd2750a3aca045563eb8af6b | trade_date_block_bootstrap | 11434 | BLOCKED | False | False | surrun_fc2d74071e8d87a6e2526f8a | UNDERPOWERED |
| sspec_fd2750a3aca045563eb8af6b | trade_date_block_bootstrap | 11435 | BLOCKED | False | False | surrun_d9ca4379e95a2608c34894a0 | UNDERPOWERED |
| sspec_f80bd0be561d17e931fb0402 | trade_date_block_bootstrap | 11436 | BLOCKED | False | True | surrun_c9685c6e248b450fdc10c0a2 | UNDERPOWERED |
| sspec_f80bd0be561d17e931fb0402 | trade_date_block_bootstrap | 11437 | BLOCKED | False | True | surrun_fdd6aa2995d349654dc8e752 | UNDERPOWERED |
| sspec_f80bd0be561d17e931fb0402 | trade_date_block_bootstrap | 11438 | BLOCKED | False | True | surrun_54395fb4ddfec62dcfe1578b | UNDERPOWERED |
| sspec_a06280dea281704c1cdc37e0 | trade_date_block_bootstrap | 11439 | BLOCKED | False | True | surrun_52b11429e00c17dca699c1d4 | UNDERPOWERED |
| sspec_a06280dea281704c1cdc37e0 | trade_date_block_bootstrap | 11440 | BLOCKED | False | True | surrun_6470258c0891804eef2face4 | UNDERPOWERED |
| sspec_a06280dea281704c1cdc37e0 | trade_date_block_bootstrap | 11441 | BLOCKED | False | True | surrun_614abb8ec5da6002925cf909 | UNDERPOWERED |
| sspec_0990309cfb9e8788be5968f7 | trade_date_block_bootstrap | 11442 | BLOCKED | False | True | surrun_567c96a42c4e82fb012523ad | UNDERPOWERED |
| sspec_0990309cfb9e8788be5968f7 | trade_date_block_bootstrap | 11443 | BLOCKED | False | True | surrun_a35c542232641a77c1d27a65 | UNDERPOWERED |
| sspec_0990309cfb9e8788be5968f7 | trade_date_block_bootstrap | 11444 | BLOCKED | False | True | surrun_b0bc90e5629617b42175d8f5 | UNDERPOWERED |
| sspec_0f9e9ad9bf8132b8922abe1f | trade_date_block_bootstrap | 11445 | BLOCKED | False | True | surrun_d9d6bd4d30445e8074c15e35 | UNDERPOWERED |
| sspec_0f9e9ad9bf8132b8922abe1f | trade_date_block_bootstrap | 11446 | BLOCKED | False | True | surrun_60249f7d6c60889a440ab989 | UNDERPOWERED |
| sspec_0f9e9ad9bf8132b8922abe1f | trade_date_block_bootstrap | 11447 | BLOCKED | False | True | surrun_973b4b4f62754a2b50161fd4 | UNDERPOWERED |
| sspec_d3a962c95c04c326a5a5b151 | trade_date_block_bootstrap | 11448 | BLOCKED | False | True | surrun_3a2e9671a85705b070353fbe | UNDERPOWERED |
| sspec_d3a962c95c04c326a5a5b151 | trade_date_block_bootstrap | 11449 | BLOCKED | False | True | surrun_a076aaf8aeab8e160570ca88 | UNDERPOWERED |
| sspec_d3a962c95c04c326a5a5b151 | trade_date_block_bootstrap | 11450 | BLOCKED | False | True | surrun_5f5d0097866adb4d8b322c7c | UNDERPOWERED |
| sspec_533ff382160faa39e06fcd0c | trade_date_block_bootstrap | 11457 | BLOCKED | False | True | surrun_0c58b15534fbf235381b4fb8 | UNDERPOWERED |
| sspec_533ff382160faa39e06fcd0c | trade_date_block_bootstrap | 11458 | BLOCKED | False | True | surrun_8380977fa33d6599cc8cdc19 | UNDERPOWERED |
| sspec_533ff382160faa39e06fcd0c | trade_date_block_bootstrap | 11459 | BLOCKED | False | True | surrun_fe9099b042c92c4919d705c0 | UNDERPOWERED |
| sspec_a65ba642712c610559cd9d3b | trade_date_block_bootstrap | 11460 | BLOCKED | False | True | surrun_3b0f89ad936d132ac6f4e1f4 | UNDERPOWERED |
| sspec_a65ba642712c610559cd9d3b | trade_date_block_bootstrap | 11461 | BLOCKED | False | True | surrun_113a5d23e8ad2bf4be561929 | UNDERPOWERED |
| sspec_a65ba642712c610559cd9d3b | trade_date_block_bootstrap | 11462 | BLOCKED | False | True | surrun_2552ef545c1bbca86f4f0210 | UNDERPOWERED |
| sspec_03c63ff6b322f6f4909a78aa | trade_date_block_bootstrap | 11463 | BLOCKED | False | True | surrun_c2f8d2d477b8386ee88ac20f | UNDERPOWERED |
| sspec_03c63ff6b322f6f4909a78aa | trade_date_block_bootstrap | 11464 | BLOCKED | False | True | surrun_dfe64a475e2808dbc135b47a | UNDERPOWERED |
| sspec_03c63ff6b322f6f4909a78aa | trade_date_block_bootstrap | 11465 | BLOCKED | False | True | surrun_a4ba80909e880635be498b2f | UNDERPOWERED |
| sspec_2a34524e556fb66946af0adc | trade_date_block_bootstrap | 11466 | BLOCKED | False | True | surrun_1eaf4a6cce460f220f272fa6 | UNDERPOWERED |
| sspec_2a34524e556fb66946af0adc | trade_date_block_bootstrap | 11467 | BLOCKED | False | True | surrun_bd6593f83523a3ffdb61b7e2 | UNDERPOWERED |
| sspec_2a34524e556fb66946af0adc | trade_date_block_bootstrap | 11468 | BLOCKED | False | True | surrun_639730997ac98f525bcba22b | UNDERPOWERED |
| sspec_261125026ac6a6a550e5489e | trade_date_block_bootstrap | 11469 | BLOCKED | False | True | surrun_052965ca5b30c124f996f0c9 | UNDERPOWERED |
| sspec_261125026ac6a6a550e5489e | trade_date_block_bootstrap | 11470 | BLOCKED | False | True | surrun_a89db63f7ae0eba432da29d1 | UNDERPOWERED |
| sspec_261125026ac6a6a550e5489e | trade_date_block_bootstrap | 11471 | BLOCKED | False | True | surrun_18815849504d0484278c14f0 | UNDERPOWERED |
| sspec_a0bc202daa195cc98c807f98 | trade_date_block_bootstrap | 11472 | BLOCKED | False | True | surrun_1eac8ff53dc1213c8ee71b82 | UNDERPOWERED |
| sspec_a0bc202daa195cc98c807f98 | trade_date_block_bootstrap | 11473 | BLOCKED | False | True | surrun_9da20d8fbb6cfb96a46a5d0c | UNDERPOWERED |
| sspec_a0bc202daa195cc98c807f98 | trade_date_block_bootstrap | 11474 | BLOCKED | False | True | surrun_e8dfe4096fe4a38183605aba | UNDERPOWERED |
| sspec_9f6259b2eea65e49428ab583 | trade_date_block_bootstrap | 11475 | BLOCKED | False | True | surrun_12120ef3030dcfb36e015bd3 | UNDERPOWERED |
| sspec_9f6259b2eea65e49428ab583 | trade_date_block_bootstrap | 11476 | BLOCKED | False | True | surrun_ba2aeaf6d318178a99b2e963 | UNDERPOWERED |
| sspec_9f6259b2eea65e49428ab583 | trade_date_block_bootstrap | 11477 | BLOCKED | False | True | surrun_bc9b475cc8de671e44b73c67 | UNDERPOWERED |
| sspec_0b07a09019e3a1181159b0b5 | trade_date_block_bootstrap | 11478 | BLOCKED | False | True | surrun_a5bd6dfab0216c121275950c | UNDERPOWERED |
| sspec_0b07a09019e3a1181159b0b5 | trade_date_block_bootstrap | 11479 | BLOCKED | False | True | surrun_2e02014f678a09a20283da10 | UNDERPOWERED |
| sspec_0b07a09019e3a1181159b0b5 | trade_date_block_bootstrap | 11480 | BLOCKED | False | True | surrun_e8c704f52a58a73998276b19 | UNDERPOWERED |
| sspec_5d095928bc776ba1a0f11bd1 | trade_date_block_bootstrap | 11487 | BLOCKED | False | True | surrun_b7424f7ec667f6567cf768e0 | UNDERPOWERED |
| sspec_5d095928bc776ba1a0f11bd1 | trade_date_block_bootstrap | 11488 | BLOCKED | False | True | surrun_fb8de2787276db0cd7230d06 | UNDERPOWERED |
| sspec_5d095928bc776ba1a0f11bd1 | trade_date_block_bootstrap | 11489 | BLOCKED | False | True | surrun_b4618a91a8f3899b0cce5abf | UNDERPOWERED |
| sspec_0c3a03aaf4a6e23d8dfd77ef | trade_date_block_bootstrap | 11490 | BLOCKED | False | True | surrun_73ddf4abc482d4a8e3e16381 | UNDERPOWERED |
| sspec_0c3a03aaf4a6e23d8dfd77ef | trade_date_block_bootstrap | 11491 | BLOCKED | False | True | surrun_a15cbf52020574334dca73ef | UNDERPOWERED |
| sspec_0c3a03aaf4a6e23d8dfd77ef | trade_date_block_bootstrap | 11492 | BLOCKED | False | True | surrun_bf43cf21ac49b717d2d922c6 | UNDERPOWERED |
| sspec_326174687ccb2d68792ed3f0 | trade_date_block_bootstrap | 11493 | BLOCKED | False | True | surrun_9c7effad4bdb2e13e14bd7d3 | UNDERPOWERED |
| sspec_326174687ccb2d68792ed3f0 | trade_date_block_bootstrap | 11494 | BLOCKED | False | True | surrun_432412c4dd57bb962e07c7cd | UNDERPOWERED |
| sspec_326174687ccb2d68792ed3f0 | trade_date_block_bootstrap | 11495 | BLOCKED | False | True | surrun_7c5c2ea3af9393509bfcdc1e | UNDERPOWERED |
| sspec_f8b2ab233a69231131a0c199 | trade_date_block_bootstrap | 11496 | BLOCKED | False | True | surrun_add87ac8b50909b33633bdf6 | UNDERPOWERED |
| sspec_f8b2ab233a69231131a0c199 | trade_date_block_bootstrap | 11497 | BLOCKED | False | True | surrun_166fe16ab46bfbbae87ce446 | UNDERPOWERED |
| sspec_f8b2ab233a69231131a0c199 | trade_date_block_bootstrap | 11498 | BLOCKED | False | True | surrun_5d39110dae4123dc1d5a14f0 | UNDERPOWERED |
| sspec_5e855370880afb3f8f73bf76 | trade_date_block_bootstrap | 11499 | BLOCKED | False | True | surrun_2d69f0d4b0456e0d8ddf4a11 | UNDERPOWERED |
| sspec_5e855370880afb3f8f73bf76 | trade_date_block_bootstrap | 11500 | BLOCKED | False | True | surrun_982b1cb59afda41d53505d57 | UNDERPOWERED |
| sspec_5e855370880afb3f8f73bf76 | trade_date_block_bootstrap | 11501 | BLOCKED | False | True | surrun_a2d84446130b8d375504e533 | UNDERPOWERED |
| sspec_c1720272123b72b14c96e51c | trade_date_block_bootstrap | 11502 | BLOCKED | False | True | surrun_1affccb4290e530e6242eff8 | UNDERPOWERED |
| sspec_c1720272123b72b14c96e51c | trade_date_block_bootstrap | 11503 | BLOCKED | False | True | surrun_056533e4c5ac17bd5b99158e | UNDERPOWERED |
| sspec_c1720272123b72b14c96e51c | trade_date_block_bootstrap | 11504 | BLOCKED | False | True | surrun_6cf61c0ca2c929f3cdbb793c | UNDERPOWERED |
| sspec_74285fdc388dd0840c14abda | trade_date_block_bootstrap | 11505 | BLOCKED | False | True | surrun_44587b2a2b6ef093d127043d | UNDERPOWERED |
| sspec_74285fdc388dd0840c14abda | trade_date_block_bootstrap | 11506 | BLOCKED | False | True | surrun_3d37b95c002ac4c358b28ca0 | UNDERPOWERED |
| sspec_74285fdc388dd0840c14abda | trade_date_block_bootstrap | 11507 | BLOCKED | False | True | surrun_981542a2d7724bac15536b28 | UNDERPOWERED |
| sspec_0260289769ca1a9d7496c1ab | trade_date_block_bootstrap | 11508 | BLOCKED | False | True | surrun_32ac40217bb3d22d60c36b27 | UNDERPOWERED |
| sspec_0260289769ca1a9d7496c1ab | trade_date_block_bootstrap | 11509 | BLOCKED | False | True | surrun_0556760cf489ba3f40ca85f0 | UNDERPOWERED |
| sspec_0260289769ca1a9d7496c1ab | trade_date_block_bootstrap | 11510 | BLOCKED | False | True | surrun_58d4f32ebde38b924cbabe06 | UNDERPOWERED |
| sspec_2449cfd728c761dbb4897c6e | trade_date_block_bootstrap | 11511 | BLOCKED | False | True | surrun_af080a930abcc3fcd61ee956 | UNDERPOWERED |
| sspec_2449cfd728c761dbb4897c6e | trade_date_block_bootstrap | 11512 | BLOCKED | False | True | surrun_00cd784ba65c9a7196eb488f | UNDERPOWERED |
| sspec_2449cfd728c761dbb4897c6e | trade_date_block_bootstrap | 11513 | BLOCKED | False | True | surrun_e9d9fa885c1e74b9a8e6dab9 | UNDERPOWERED |
| sspec_684f569d85f1988a509d28df | trade_date_block_bootstrap | 11517 | BLOCKED | False | True | surrun_c807f1af7ff62e5a64c5d208 | UNDERPOWERED |
| sspec_684f569d85f1988a509d28df | trade_date_block_bootstrap | 11518 | BLOCKED | False | True | surrun_b14038cd29db72ba9700a4e3 | UNDERPOWERED |
| sspec_684f569d85f1988a509d28df | trade_date_block_bootstrap | 11519 | BLOCKED | False | True | surrun_00fa3ead3f5406b16b3ab253 | UNDERPOWERED |
| sspec_3afca631bbe2f9154d755d7b | trade_date_block_bootstrap | 11520 | BLOCKED | False | True | surrun_06cd770dfdaf38a8bd203bfa | UNDERPOWERED |
| sspec_3afca631bbe2f9154d755d7b | trade_date_block_bootstrap | 11521 | BLOCKED | False | True | surrun_f064632bbf9de5525491cf3f | UNDERPOWERED |
| sspec_3afca631bbe2f9154d755d7b | trade_date_block_bootstrap | 11522 | BLOCKED | False | True | surrun_84fc1844a7c8c1cf4e631df9 | UNDERPOWERED |
| sspec_419d162d9b178838f63fbba6 | trade_date_block_bootstrap | 11523 | BLOCKED | False | True | surrun_823943ad137b19bf3691792d | UNDERPOWERED |
| sspec_419d162d9b178838f63fbba6 | trade_date_block_bootstrap | 11524 | BLOCKED | False | True | surrun_174d76d3a762e337a643770a | UNDERPOWERED |
| sspec_419d162d9b178838f63fbba6 | trade_date_block_bootstrap | 11525 | BLOCKED | False | True | surrun_e25308292026e6bfdd8e16a1 | UNDERPOWERED |
| sspec_110935b21bde6f964d90d4a7 | trade_date_block_bootstrap | 11526 | BLOCKED | False | True | surrun_1d89aad216850bdc1c8d4e03 | UNDERPOWERED |
| sspec_110935b21bde6f964d90d4a7 | trade_date_block_bootstrap | 11527 | BLOCKED | False | True | surrun_6d34a1348a83feacdc60fb27 | UNDERPOWERED |
| sspec_110935b21bde6f964d90d4a7 | trade_date_block_bootstrap | 11528 | BLOCKED | False | True | surrun_f0f0685b5b7bb3c3d4ad9380 | UNDERPOWERED |
| sspec_33fcb8fb7b545b04a44b319d | trade_date_block_bootstrap | 11529 | BLOCKED | False | True | surrun_da94ef4eec76affda3f59ae0 | UNDERPOWERED |
| sspec_33fcb8fb7b545b04a44b319d | trade_date_block_bootstrap | 11530 | BLOCKED | False | True | surrun_867a4f1ad8ec05e56fbf861d | UNDERPOWERED |
| sspec_33fcb8fb7b545b04a44b319d | trade_date_block_bootstrap | 11531 | BLOCKED | False | True | surrun_625a46404bf22d3c89bce853 | UNDERPOWERED |
| sspec_0d623cae8deb36756baca119 | trade_date_block_bootstrap | 11532 | BLOCKED | False | True | surrun_d73a324c2f071646f4b5b83b | UNDERPOWERED |
| sspec_0d623cae8deb36756baca119 | trade_date_block_bootstrap | 11533 | BLOCKED | False | True | surrun_40da0fe65e09d0d1cf968fa8 | UNDERPOWERED |
| sspec_0d623cae8deb36756baca119 | trade_date_block_bootstrap | 11534 | BLOCKED | False | True | surrun_75f02e78901e0ddc99c18489 | UNDERPOWERED |
| sspec_258b8c65196e47840b4296de | trade_date_block_bootstrap | 11535 | BLOCKED | False | True | surrun_16591c1274a151fde4ec48d6 | UNDERPOWERED |
| sspec_258b8c65196e47840b4296de | trade_date_block_bootstrap | 11536 | BLOCKED | False | True | surrun_fce1350b1b136e52ebe25293 | UNDERPOWERED |
| sspec_258b8c65196e47840b4296de | trade_date_block_bootstrap | 11537 | BLOCKED | False | True | surrun_d829c2e0867f72b13a713d0b | UNDERPOWERED |
| sspec_33631390a4e6ed27b3c324f6 | trade_date_block_bootstrap | 11538 | BLOCKED | False | True | surrun_6563a4744d3c0ad1b9f05381 | UNDERPOWERED |
| sspec_33631390a4e6ed27b3c324f6 | trade_date_block_bootstrap | 11539 | BLOCKED | False | True | surrun_370a5fa6547036ccf097186d | UNDERPOWERED |
| sspec_33631390a4e6ed27b3c324f6 | trade_date_block_bootstrap | 11540 | BLOCKED | False | True | surrun_36947ab70fb3b4bdc1dacb20 | UNDERPOWERED |
| sspec_e28787de9a4e7464687e8697 | trade_date_block_bootstrap | 11547 | BLOCKED | False | True | surrun_8ad8fe2fa788d91830a4495a | UNDERPOWERED |
| sspec_e28787de9a4e7464687e8697 | trade_date_block_bootstrap | 11548 | BLOCKED | False | True | surrun_21624bf1d568fccbffceba45 | UNDERPOWERED |
| sspec_e28787de9a4e7464687e8697 | trade_date_block_bootstrap | 11549 | BLOCKED | False | True | surrun_0f3bb9f705d39f82214fd3bf | UNDERPOWERED |
| sspec_74bd3bba2a9b74061e760954 | trade_date_block_bootstrap | 11550 | BLOCKED | False | True | surrun_8a58a02b807f06858449c553 | UNDERPOWERED |
| sspec_74bd3bba2a9b74061e760954 | trade_date_block_bootstrap | 11551 | BLOCKED | False | True | surrun_1478169055cbfaf539c81868 | UNDERPOWERED |
| sspec_74bd3bba2a9b74061e760954 | trade_date_block_bootstrap | 11552 | BLOCKED | False | True | surrun_83d37a771dbf7c747311719c | UNDERPOWERED |
| sspec_9908d0bed53f48739f812f9d | trade_date_block_bootstrap | 11553 | BLOCKED | False | True | surrun_56da3248ebcc8f941b63200a | UNDERPOWERED |
| sspec_9908d0bed53f48739f812f9d | trade_date_block_bootstrap | 11554 | BLOCKED | False | True | surrun_7943aee79b86d2df56f264d1 | UNDERPOWERED |
| sspec_9908d0bed53f48739f812f9d | trade_date_block_bootstrap | 11555 | BLOCKED | False | True | surrun_59f626a6f06a0f0135a545e1 | UNDERPOWERED |
| sspec_b5521a0d1fd11a9d1844e00c | trade_date_block_bootstrap | 11556 | BLOCKED | False | True | surrun_6ce074f2a3130c75c8d43a98 | UNDERPOWERED |
| sspec_b5521a0d1fd11a9d1844e00c | trade_date_block_bootstrap | 11557 | BLOCKED | False | True | surrun_32b676c1d731657f58c63ef0 | UNDERPOWERED |
| sspec_b5521a0d1fd11a9d1844e00c | trade_date_block_bootstrap | 11558 | BLOCKED | False | True | surrun_492a8b41563b84050d03abb7 | UNDERPOWERED |
| sspec_1498f0d43ca61760f6f6955a | trade_date_block_bootstrap | 11559 | BLOCKED | False | True | surrun_dd2642a46974acb49589bfa9 | UNDERPOWERED |
| sspec_1498f0d43ca61760f6f6955a | trade_date_block_bootstrap | 11560 | BLOCKED | False | True | surrun_b397d6e1bcc8a90461dbf50d | UNDERPOWERED |
| sspec_1498f0d43ca61760f6f6955a | trade_date_block_bootstrap | 11561 | BLOCKED | False | True | surrun_43d54d5cbba275941af83b54 | UNDERPOWERED |
| sspec_9a9c79322b265c5f8129ed12 | trade_date_block_bootstrap | 11562 | BLOCKED | False | True | surrun_98345a875163f97a236c0e7a | UNDERPOWERED |
| sspec_9a9c79322b265c5f8129ed12 | trade_date_block_bootstrap | 11563 | BLOCKED | False | True | surrun_157491cfc2036494a4a06342 | UNDERPOWERED |
| sspec_9a9c79322b265c5f8129ed12 | trade_date_block_bootstrap | 11564 | BLOCKED | False | True | surrun_73e1b23a1a2bb51315090210 | UNDERPOWERED |
| sspec_9049fbde7d9bbd46c41f277c | trade_date_block_bootstrap | 11565 | BLOCKED | False | True | surrun_e8056471297a03673ece53d9 | UNDERPOWERED |
| sspec_9049fbde7d9bbd46c41f277c | trade_date_block_bootstrap | 11566 | BLOCKED | False | True | surrun_686ac3e2a15b1f95c33ddd6d | UNDERPOWERED |
| sspec_9049fbde7d9bbd46c41f277c | trade_date_block_bootstrap | 11567 | BLOCKED | False | True | surrun_0588cecb626e78df69ba7ce1 | UNDERPOWERED |
| sspec_1ac6a5e12e6a3eaaa7e3414c | trade_date_block_bootstrap | 11568 | BLOCKED | False | True | surrun_5f6b013f78a7f336cc61852b | UNDERPOWERED |
| sspec_1ac6a5e12e6a3eaaa7e3414c | trade_date_block_bootstrap | 11569 | BLOCKED | False | True | surrun_8a4af7e5c2d770dd6d4349cf | UNDERPOWERED |
| sspec_1ac6a5e12e6a3eaaa7e3414c | trade_date_block_bootstrap | 11570 | BLOCKED | False | True | surrun_7f194883e711cc0cc1b3d937 | UNDERPOWERED |
| sspec_8657025ea76ba672da9865b2 | trade_date_block_bootstrap | 11571 | BLOCKED | False | True | surrun_4ddf66eaf1d4543a48b1e462 | UNDERPOWERED |
| sspec_8657025ea76ba672da9865b2 | trade_date_block_bootstrap | 11572 | BLOCKED | False | True | surrun_317da26a1ae5dda27c6031c1 | UNDERPOWERED |
| sspec_8657025ea76ba672da9865b2 | trade_date_block_bootstrap | 11573 | BLOCKED | False | True | surrun_34655bb188f175129dbc2b2e | UNDERPOWERED |
| sspec_ac849ae4faf8a18a91083d1e | trade_date_block_bootstrap | 11577 | BLOCKED | False | True | surrun_ddd37585a19e30e3f24b5491 | UNDERPOWERED |
| sspec_ac849ae4faf8a18a91083d1e | trade_date_block_bootstrap | 11578 | BLOCKED | False | True | surrun_c8f08e63ed6ac6003bd2c1fe | UNDERPOWERED |
| sspec_ac849ae4faf8a18a91083d1e | trade_date_block_bootstrap | 11579 | BLOCKED | False | True | surrun_7faf9ee6e549cafdf17eefc5 | UNDERPOWERED |
| sspec_f69c57c06e4a85a0125a7550 | trade_date_block_bootstrap | 11580 | BLOCKED | False | True | surrun_1de3047968dbf81905e7c952 | UNDERPOWERED |
| sspec_f69c57c06e4a85a0125a7550 | trade_date_block_bootstrap | 11581 | BLOCKED | False | True | surrun_db71f991d5e2f7ecabac6723 | UNDERPOWERED |
| sspec_f69c57c06e4a85a0125a7550 | trade_date_block_bootstrap | 11582 | BLOCKED | False | True | surrun_33ef972f9233a6437abf965a | UNDERPOWERED |
| sspec_46a94b704408745064e26d67 | trade_date_block_bootstrap | 11583 | BLOCKED | False | True | surrun_d04de5f87ab1663eb8fada3a | UNDERPOWERED |
| sspec_46a94b704408745064e26d67 | trade_date_block_bootstrap | 11584 | BLOCKED | False | True | surrun_e4cbedac440ec73827ccdd82 | UNDERPOWERED |
| sspec_46a94b704408745064e26d67 | trade_date_block_bootstrap | 11585 | BLOCKED | False | True | surrun_cb4a1082ce373ca0b4d5ca3b | UNDERPOWERED |
| sspec_49511a9f49603b66d5d66c83 | trade_date_block_bootstrap | 11586 | BLOCKED | False | True | surrun_a429a3fe8c8a3b9617a1dee1 | UNDERPOWERED |
| sspec_49511a9f49603b66d5d66c83 | trade_date_block_bootstrap | 11587 | BLOCKED | False | True | surrun_8f4e3c1057fce5fa330c8464 | UNDERPOWERED |
| sspec_49511a9f49603b66d5d66c83 | trade_date_block_bootstrap | 11588 | BLOCKED | False | True | surrun_29d3abfe35b5973a5a35882a | UNDERPOWERED |
| sspec_fcf3c12b6e3e90ebd53933c5 | trade_date_block_bootstrap | 11589 | BLOCKED | False | True | surrun_d6a3b85369a9e841c905d89a | UNDERPOWERED |
| sspec_fcf3c12b6e3e90ebd53933c5 | trade_date_block_bootstrap | 11590 | BLOCKED | False | True | surrun_655b10de604406b091aa9107 | UNDERPOWERED |
| sspec_fcf3c12b6e3e90ebd53933c5 | trade_date_block_bootstrap | 11591 | BLOCKED | False | True | surrun_49fd1212b01d8ce68c497552 | UNDERPOWERED |
| sspec_be01b9679a0cd39454383b4d | trade_date_block_bootstrap | 11592 | BLOCKED | False | True | surrun_21b49df953d3234698ab0714 | UNDERPOWERED |
| sspec_be01b9679a0cd39454383b4d | trade_date_block_bootstrap | 11593 | BLOCKED | False | True | surrun_6f98ae064381eb2bf3f6cbaf | UNDERPOWERED |
| sspec_be01b9679a0cd39454383b4d | trade_date_block_bootstrap | 11594 | BLOCKED | False | True | surrun_0cf0cfd130ca400b23adca52 | UNDERPOWERED |
| sspec_4dd2be6e491ac64ff5a955be | trade_date_block_bootstrap | 11595 | BLOCKED | False | True | surrun_8593b32e05b239a57fddd702 | UNDERPOWERED |
| sspec_4dd2be6e491ac64ff5a955be | trade_date_block_bootstrap | 11596 | BLOCKED | False | True | surrun_080ecb03705e1369c58ae55d | UNDERPOWERED |
| sspec_4dd2be6e491ac64ff5a955be | trade_date_block_bootstrap | 11597 | BLOCKED | False | True | surrun_c0d8a2a74c9b2fbe04ae98c6 | UNDERPOWERED |
| sspec_9815a44d3c2bcd03430deb87 | trade_date_block_bootstrap | 11598 | BLOCKED | False | True | surrun_c20b55272fe718d49dbaf888 | UNDERPOWERED |
| sspec_9815a44d3c2bcd03430deb87 | trade_date_block_bootstrap | 11599 | BLOCKED | False | True | surrun_6c6f20ae59ee3b1225079cba | UNDERPOWERED |
| sspec_9815a44d3c2bcd03430deb87 | trade_date_block_bootstrap | 11600 | BLOCKED | False | True | surrun_4bb7b74124a3e41f4496c7cb | UNDERPOWERED |
| sspec_2d39312d8d157477e82a8c6f | trade_date_block_bootstrap | 11607 | BLOCKED | False | True | surrun_f8a32e5354386cadbafca425 | UNDERPOWERED |
| sspec_2d39312d8d157477e82a8c6f | trade_date_block_bootstrap | 11608 | BLOCKED | False | True | surrun_7f0faed2e590ab74e51700e6 | UNDERPOWERED |
| sspec_2d39312d8d157477e82a8c6f | trade_date_block_bootstrap | 11609 | BLOCKED | False | True | surrun_2a2c1b3f6d44c67670b88639 | UNDERPOWERED |
| sspec_0d786a51a32f55701d86cc9b | trade_date_block_bootstrap | 11610 | BLOCKED | False | True | surrun_41611f38ee515d64be43ab14 | UNDERPOWERED |
| sspec_0d786a51a32f55701d86cc9b | trade_date_block_bootstrap | 11611 | BLOCKED | False | True | surrun_4d8462f80162818f48014bc1 | UNDERPOWERED |
| sspec_0d786a51a32f55701d86cc9b | trade_date_block_bootstrap | 11612 | BLOCKED | False | True | surrun_1295574cdc5955393f308910 | UNDERPOWERED |
| sspec_691e00c3a46428a3157d8ec1 | trade_date_block_bootstrap | 11613 | BLOCKED | False | True | surrun_376a97362b28ce5122f33f8e | UNDERPOWERED |
| sspec_691e00c3a46428a3157d8ec1 | trade_date_block_bootstrap | 11614 | BLOCKED | False | True | surrun_975ffe708c57389c3084ac6b | UNDERPOWERED |
| sspec_691e00c3a46428a3157d8ec1 | trade_date_block_bootstrap | 11615 | BLOCKED | False | True | surrun_ab1607f8140b1016b44a50f6 | UNDERPOWERED |
| sspec_7e696c51356012e9433a9108 | trade_date_block_bootstrap | 11616 | BLOCKED | False | True | surrun_46a4ee5c545592c7d0059883 | UNDERPOWERED |
| sspec_7e696c51356012e9433a9108 | trade_date_block_bootstrap | 11617 | BLOCKED | False | True | surrun_cf7752a5488e5cd8b9ae1ae3 | UNDERPOWERED |
| sspec_7e696c51356012e9433a9108 | trade_date_block_bootstrap | 11618 | BLOCKED | False | True | surrun_fb01d3e575208db03bc091fe | UNDERPOWERED |
| sspec_65975eb5177404e4e861011c | trade_date_block_bootstrap | 11619 | BLOCKED | False | True | surrun_fb6f9e109b5a9bf0ecbb4f29 | UNDERPOWERED |
| sspec_65975eb5177404e4e861011c | trade_date_block_bootstrap | 11620 | BLOCKED | False | True | surrun_edfcf78e11fa8eb31b1417cc | UNDERPOWERED |
| sspec_65975eb5177404e4e861011c | trade_date_block_bootstrap | 11621 | BLOCKED | False | True | surrun_876c710224241118be77f17b | UNDERPOWERED |
| sspec_82772f708fb53fb992481605 | trade_date_block_bootstrap | 11622 | BLOCKED | False | True | surrun_fe5bfbeab0638b9c0563f153 | UNDERPOWERED |
| sspec_82772f708fb53fb992481605 | trade_date_block_bootstrap | 11623 | BLOCKED | False | True | surrun_78ad14e60949d44e4955bffb | UNDERPOWERED |
| sspec_82772f708fb53fb992481605 | trade_date_block_bootstrap | 11624 | BLOCKED | False | True | surrun_17c60d16d980dab82606ddd6 | UNDERPOWERED |
| sspec_d2a04824cab2216f85e4b8c7 | trade_date_block_bootstrap | 11625 | BLOCKED | False | True | surrun_bb6c48190fec31c912b48c15 | UNDERPOWERED |
| sspec_d2a04824cab2216f85e4b8c7 | trade_date_block_bootstrap | 11626 | BLOCKED | False | True | surrun_6723ea6c9e149806becafd55 | UNDERPOWERED |
| sspec_d2a04824cab2216f85e4b8c7 | trade_date_block_bootstrap | 11627 | BLOCKED | False | True | surrun_75f19ff6c093c19bcac9f12b | UNDERPOWERED |
| sspec_95e8550f25151503fd62881a | trade_date_block_bootstrap | 11628 | BLOCKED | False | True | surrun_d25064358ac6a250098d8c8d | UNDERPOWERED |
| sspec_95e8550f25151503fd62881a | trade_date_block_bootstrap | 11629 | BLOCKED | False | True | surrun_b22a1f102a64b8c9fdde81c8 | UNDERPOWERED |
| sspec_95e8550f25151503fd62881a | trade_date_block_bootstrap | 11630 | BLOCKED | False | True | surrun_c901afc6f21d51d2c768e927 | UNDERPOWERED |
| sspec_cad600c7e7ae82ee371f300d | trade_date_block_bootstrap | 11637 | BLOCKED | False | True | surrun_5f23e126f879504fe23d8c10 | UNDERPOWERED |
| sspec_cad600c7e7ae82ee371f300d | trade_date_block_bootstrap | 11638 | BLOCKED | False | True | surrun_84e7cff6753b53dce550f64f | UNDERPOWERED |
| sspec_cad600c7e7ae82ee371f300d | trade_date_block_bootstrap | 11639 | BLOCKED | False | True | surrun_9b8b1f9345e6b83765bc77e0 | UNDERPOWERED |
| sspec_393c8161beb74ba83f5a164b | trade_date_block_bootstrap | 11640 | BLOCKED | False | True | surrun_4c303bb676d0786b61893fd7 | UNDERPOWERED |
| sspec_393c8161beb74ba83f5a164b | trade_date_block_bootstrap | 11641 | BLOCKED | False | True | surrun_587a5bf5a0c3edadc386495b | UNDERPOWERED |
| sspec_393c8161beb74ba83f5a164b | trade_date_block_bootstrap | 11642 | BLOCKED | False | True | surrun_5c99bae55bd8805be446b781 | UNDERPOWERED |
| sspec_974ff4d3b7738064e6dff75f | trade_date_block_bootstrap | 11643 | BLOCKED | False | True | surrun_22391b0d7f233727a5266fcc | UNDERPOWERED |
| sspec_974ff4d3b7738064e6dff75f | trade_date_block_bootstrap | 11644 | BLOCKED | False | True | surrun_2e3d1c4eae423e4ad9cb468f | UNDERPOWERED |
| sspec_974ff4d3b7738064e6dff75f | trade_date_block_bootstrap | 11645 | BLOCKED | False | True | surrun_473f3587dffc3a4062142f1d | UNDERPOWERED |
| sspec_df4c90ce1bae0acccd4d13d9 | trade_date_block_bootstrap | 11646 | BLOCKED | False | True | surrun_56e3c2d8984c162b92ed07d4 | UNDERPOWERED |
| sspec_df4c90ce1bae0acccd4d13d9 | trade_date_block_bootstrap | 11647 | BLOCKED | False | True | surrun_1ad861dbd490fed1540f7360 | UNDERPOWERED |
| sspec_df4c90ce1bae0acccd4d13d9 | trade_date_block_bootstrap | 11648 | BLOCKED | False | True | surrun_e55e13d8e43decdfd015ec25 | UNDERPOWERED |
| sspec_3b888310b6e62e8b4aa4f581 | trade_date_block_bootstrap | 11649 | BLOCKED | False | True | surrun_b6b523c3549a079eac9eb2da | UNDERPOWERED |
| sspec_3b888310b6e62e8b4aa4f581 | trade_date_block_bootstrap | 11650 | BLOCKED | False | True | surrun_477b84d1b8687eeccd6f5299 | UNDERPOWERED |
| sspec_3b888310b6e62e8b4aa4f581 | trade_date_block_bootstrap | 11651 | BLOCKED | False | True | surrun_724a789b1062c58dc7997907 | UNDERPOWERED |
| sspec_0501ae1937d72076f88c76aa | trade_date_block_bootstrap | 11652 | BLOCKED | False | True | surrun_63267dcfc299faea74f0f073 | UNDERPOWERED |
| sspec_0501ae1937d72076f88c76aa | trade_date_block_bootstrap | 11653 | BLOCKED | False | True | surrun_874ecf4b58c128b10c12c4c3 | UNDERPOWERED |
| sspec_0501ae1937d72076f88c76aa | trade_date_block_bootstrap | 11654 | BLOCKED | False | True | surrun_8db3b923486ddf52ea618e4d | UNDERPOWERED |
| sspec_64628498470d067426f90bc7 | trade_date_block_bootstrap | 11655 | BLOCKED | False | True | surrun_add2ae136114272721556835 | UNDERPOWERED |
| sspec_64628498470d067426f90bc7 | trade_date_block_bootstrap | 11656 | BLOCKED | False | True | surrun_3d0276fa721edb302e4a6ed8 | UNDERPOWERED |
| sspec_64628498470d067426f90bc7 | trade_date_block_bootstrap | 11657 | BLOCKED | False | True | surrun_bc7c23ce41ac8d6a2df46a59 | UNDERPOWERED |
| sspec_818ff30a836a7109b0197261 | trade_date_block_bootstrap | 11658 | BLOCKED | False | True | surrun_e6959d15479d12496dfa783a | UNDERPOWERED |
| sspec_818ff30a836a7109b0197261 | trade_date_block_bootstrap | 11659 | BLOCKED | False | True | surrun_43c77a3ed8cc0254d39fdc4b | UNDERPOWERED |
| sspec_818ff30a836a7109b0197261 | trade_date_block_bootstrap | 11660 | BLOCKED | False | True | surrun_b06c234ca8cc0ee0901ad321 | UNDERPOWERED |
| sspec_61916013e1c79796eb3a2b70 | trade_date_block_bootstrap | 11667 | BLOCKED | False | True | surrun_6d0319a9d7e4eeb43ca30c7f | UNDERPOWERED |
| sspec_61916013e1c79796eb3a2b70 | trade_date_block_bootstrap | 11668 | BLOCKED | False | True | surrun_313da3506e11eb369fe5fa9a | UNDERPOWERED |
| sspec_61916013e1c79796eb3a2b70 | trade_date_block_bootstrap | 11669 | BLOCKED | False | True | surrun_70732e02779dbb256a7f40e4 | UNDERPOWERED |
| sspec_2c45062ddc0fd1c1fd6d5659 | trade_date_block_bootstrap | 11670 | BLOCKED | False | True | surrun_db7b29984eeacf5a7182a530 | UNDERPOWERED |
| sspec_2c45062ddc0fd1c1fd6d5659 | trade_date_block_bootstrap | 11671 | BLOCKED | False | True | surrun_9db262e54a1f3edfd90ba3d0 | UNDERPOWERED |
| sspec_2c45062ddc0fd1c1fd6d5659 | trade_date_block_bootstrap | 11672 | BLOCKED | False | True | surrun_0096c0bee3956680c6bfe954 | UNDERPOWERED |
| sspec_7b23272b2bfb00ace9f93c9d | trade_date_block_bootstrap | 11673 | BLOCKED | False | True | surrun_84fb1528f1241874b6f0e91f | UNDERPOWERED |
| sspec_7b23272b2bfb00ace9f93c9d | trade_date_block_bootstrap | 11674 | BLOCKED | False | True | surrun_09c083b6d77db65ae86ecf33 | UNDERPOWERED |
| sspec_7b23272b2bfb00ace9f93c9d | trade_date_block_bootstrap | 11675 | BLOCKED | False | True | surrun_835a096b649a9354f0e91c4c | UNDERPOWERED |
| sspec_eccb7e90a6240aca1907d921 | trade_date_block_bootstrap | 11676 | BLOCKED | False | True | surrun_fba129a74757aaf2030192a9 | UNDERPOWERED |
| sspec_eccb7e90a6240aca1907d921 | trade_date_block_bootstrap | 11677 | BLOCKED | False | True | surrun_de08336b77a42477ef28ce98 | UNDERPOWERED |
| sspec_eccb7e90a6240aca1907d921 | trade_date_block_bootstrap | 11678 | BLOCKED | False | True | surrun_20b67a9920f21b4261298719 | UNDERPOWERED |
| sspec_0c5f89a5241378dea3b88500 | trade_date_block_bootstrap | 11679 | BLOCKED | False | True | surrun_c822fd62346109669db1d034 | UNDERPOWERED |
| sspec_0c5f89a5241378dea3b88500 | trade_date_block_bootstrap | 11680 | BLOCKED | False | True | surrun_52e03b34aab356754fbfc693 | UNDERPOWERED |
| sspec_0c5f89a5241378dea3b88500 | trade_date_block_bootstrap | 11681 | BLOCKED | False | True | surrun_94699363cf384ab64e14c57f | UNDERPOWERED |
| sspec_1c10af416dbef79d161428fa | trade_date_block_bootstrap | 11682 | BLOCKED | False | True | surrun_eddc707fa68a50aaf122f0f1 | UNDERPOWERED |
| sspec_1c10af416dbef79d161428fa | trade_date_block_bootstrap | 11683 | BLOCKED | False | True | surrun_c75673ac914cf9b703725769 | UNDERPOWERED |
| sspec_1c10af416dbef79d161428fa | trade_date_block_bootstrap | 11684 | BLOCKED | False | True | surrun_b37070676321814a2f02da46 | UNDERPOWERED |
| sspec_41cb322e5ba5146a0e377c35 | trade_date_block_bootstrap | 11685 | BLOCKED | False | True | surrun_2f589b818907160b51e7e567 | UNDERPOWERED |
| sspec_41cb322e5ba5146a0e377c35 | trade_date_block_bootstrap | 11686 | BLOCKED | False | True | surrun_ffd731fe0a1c990b0dee1631 | UNDERPOWERED |
| sspec_41cb322e5ba5146a0e377c35 | trade_date_block_bootstrap | 11687 | BLOCKED | False | True | surrun_d61be6890f1fb80caf8b1af8 | UNDERPOWERED |
| sspec_5f738d58e8c7cbb1044d4531 | trade_date_block_bootstrap | 11688 | BLOCKED | False | True | surrun_a21797e0b837b5dfb89c990c | UNDERPOWERED |
| sspec_5f738d58e8c7cbb1044d4531 | trade_date_block_bootstrap | 11689 | BLOCKED | False | True | surrun_3fe519c496363a79647dda51 | UNDERPOWERED |
| sspec_5f738d58e8c7cbb1044d4531 | trade_date_block_bootstrap | 11690 | BLOCKED | False | True | surrun_3405597d298462aea5268f96 | UNDERPOWERED |
| sspec_0c843327bc4db32869d60670 | trade_date_block_bootstrap | 11697 | BLOCKED | False | True | surrun_d2373a35a4caf13b3b130ae7 | UNDERPOWERED |
| sspec_0c843327bc4db32869d60670 | trade_date_block_bootstrap | 11698 | BLOCKED | False | True | surrun_e9f34a381407133b1968f9f5 | UNDERPOWERED |
| sspec_0c843327bc4db32869d60670 | trade_date_block_bootstrap | 11699 | BLOCKED | False | True | surrun_b32ac73a4bbd1577c6b75e50 | UNDERPOWERED |
| sspec_24ccd2d37bab9f3af31a4837 | trade_date_block_bootstrap | 11700 | BLOCKED | False | True | surrun_f45e75d47c20d4e1f26df1f6 | UNDERPOWERED |
| sspec_24ccd2d37bab9f3af31a4837 | trade_date_block_bootstrap | 11701 | BLOCKED | False | True | surrun_edd7965a2e92ff0dcb3321c1 | UNDERPOWERED |
| sspec_24ccd2d37bab9f3af31a4837 | trade_date_block_bootstrap | 11702 | BLOCKED | False | True | surrun_4bc396835fd1f8b43ba4e969 | UNDERPOWERED |
| sspec_070f899e3376d506f37a514b | trade_date_block_bootstrap | 11703 | BLOCKED | False | True | surrun_fafa24534c9ab5f5a31e3027 | UNDERPOWERED |
| sspec_070f899e3376d506f37a514b | trade_date_block_bootstrap | 11704 | BLOCKED | False | True | surrun_430854a4c80fc2a20373dbf6 | UNDERPOWERED |
| sspec_070f899e3376d506f37a514b | trade_date_block_bootstrap | 11705 | BLOCKED | False | True | surrun_3e5cc13d1cc7cc94e1d93e26 | UNDERPOWERED |
| sspec_c5eb834b3c0c2da9102e1bf0 | trade_date_block_bootstrap | 11706 | BLOCKED | False | True | surrun_86398ab1ad48b9b22b66d763 | UNDERPOWERED |
| sspec_c5eb834b3c0c2da9102e1bf0 | trade_date_block_bootstrap | 11707 | BLOCKED | False | True | surrun_b0be597fe2456c810ccf71d5 | UNDERPOWERED |
| sspec_c5eb834b3c0c2da9102e1bf0 | trade_date_block_bootstrap | 11708 | BLOCKED | False | True | surrun_0baf054a376e352afed35b4d | UNDERPOWERED |
| sspec_27a6973546c9dbee1895c59e | trade_date_block_bootstrap | 11709 | BLOCKED | False | True | surrun_ba31bd12c148ef8bb2b6cf54 | UNDERPOWERED |
| sspec_27a6973546c9dbee1895c59e | trade_date_block_bootstrap | 11710 | BLOCKED | False | True | surrun_6bdca7107505c7040526eeee | UNDERPOWERED |
| sspec_27a6973546c9dbee1895c59e | trade_date_block_bootstrap | 11711 | BLOCKED | False | True | surrun_cecd338bb212b9999645d507 | UNDERPOWERED |
| sspec_6f00aad98600d03ac168ec59 | trade_date_block_bootstrap | 11712 | BLOCKED | False | True | surrun_633a44a1292b1849e927be1d | UNDERPOWERED |
| sspec_6f00aad98600d03ac168ec59 | trade_date_block_bootstrap | 11713 | BLOCKED | False | True | surrun_3772ac299f5a764c730c1a99 | UNDERPOWERED |
| sspec_6f00aad98600d03ac168ec59 | trade_date_block_bootstrap | 11714 | BLOCKED | False | True | surrun_63d49861ee71e8c9339cc405 | UNDERPOWERED |
| sspec_18babac6084336d9e0d0354f | trade_date_block_bootstrap | 11727 | BLOCKED | False | True | surrun_006c09ca1a4f4318062f1bee | UNDERPOWERED |
| sspec_18babac6084336d9e0d0354f | trade_date_block_bootstrap | 11728 | BLOCKED | False | True | surrun_7115ae02eb2bd6e7cc3d4b7b | UNDERPOWERED |
| sspec_18babac6084336d9e0d0354f | trade_date_block_bootstrap | 11729 | BLOCKED | False | True | surrun_b05cf7a177ce1b04b9aca677 | UNDERPOWERED |
| sspec_3c850fb9543b35da6dc851ed | trade_date_block_bootstrap | 11730 | BLOCKED | False | True | surrun_feda7e049cb9d07dd31c18bb | UNDERPOWERED |
| sspec_3c850fb9543b35da6dc851ed | trade_date_block_bootstrap | 11731 | BLOCKED | False | True | surrun_3b51ec917ad9cdb3834b58a5 | UNDERPOWERED |
| sspec_3c850fb9543b35da6dc851ed | trade_date_block_bootstrap | 11732 | BLOCKED | False | True | surrun_cbee9ea023185a43eff95ae7 | UNDERPOWERED |
| sspec_d8631bd19935f7ce41733cb9 | trade_date_block_bootstrap | 11733 | BLOCKED | False | True | surrun_ae35f1976bfecbfc1fc96a7d | UNDERPOWERED |
| sspec_d8631bd19935f7ce41733cb9 | trade_date_block_bootstrap | 11734 | BLOCKED | False | True | surrun_332e85294cff7bfce3fa155b | UNDERPOWERED |
| sspec_d8631bd19935f7ce41733cb9 | trade_date_block_bootstrap | 11735 | BLOCKED | False | True | surrun_9c0e7cf64fa48859e16ab60b | UNDERPOWERED |
| sspec_3a2b5f926d2788acbb0458fb | trade_date_block_bootstrap | 11736 | BLOCKED | False | True | surrun_6fa1ca599bf74cf3ff6a5e34 | UNDERPOWERED |
| sspec_3a2b5f926d2788acbb0458fb | trade_date_block_bootstrap | 11737 | BLOCKED | False | True | surrun_e4e460cbc05cec9acba9f966 | UNDERPOWERED |
| sspec_3a2b5f926d2788acbb0458fb | trade_date_block_bootstrap | 11738 | BLOCKED | False | True | surrun_476cf0722fe6ebedfdeee71b | UNDERPOWERED |
| sspec_b4590e215f35a7ed9a143b3e | trade_date_block_bootstrap | 11739 | BLOCKED | False | True | surrun_bfd2d094964fde0e4901cdc7 | UNDERPOWERED |
| sspec_b4590e215f35a7ed9a143b3e | trade_date_block_bootstrap | 11740 | BLOCKED | False | True | surrun_5fe96d62ea6533a155305ad4 | UNDERPOWERED |
| sspec_b4590e215f35a7ed9a143b3e | trade_date_block_bootstrap | 11741 | BLOCKED | False | True | surrun_082be15c9b1ff8280bd0e19c | UNDERPOWERED |
| sspec_a4eab43fc2a064ff857ad0fa | trade_date_block_bootstrap | 11742 | BLOCKED | False | True | surrun_9b4fb30d97d72f69fab64e55 | UNDERPOWERED |
| sspec_a4eab43fc2a064ff857ad0fa | trade_date_block_bootstrap | 11743 | BLOCKED | False | True | surrun_4464917ec038301317780359 | UNDERPOWERED |
| sspec_a4eab43fc2a064ff857ad0fa | trade_date_block_bootstrap | 11744 | BLOCKED | False | True | surrun_83fe075cf0d3f52ff7f792a3 | UNDERPOWERED |
| sspec_babef3f82448347395278c8a | trade_date_block_bootstrap | 11745 | BLOCKED | False | True | surrun_77ef0756cca4efe1f982d2f6 | UNDERPOWERED |
| sspec_babef3f82448347395278c8a | trade_date_block_bootstrap | 11746 | BLOCKED | False | True | surrun_2186211a44787aa869384a7f | UNDERPOWERED |
| sspec_babef3f82448347395278c8a | trade_date_block_bootstrap | 11747 | BLOCKED | False | True | surrun_221f870f0085e747cedb17e1 | UNDERPOWERED |
| sspec_b51d27525273a2d7b303e330 | trade_date_block_bootstrap | 11748 | BLOCKED | False | True | surrun_3d3b7c40a98ac7a63ee901b9 | UNDERPOWERED |
| sspec_b51d27525273a2d7b303e330 | trade_date_block_bootstrap | 11749 | BLOCKED | False | True | surrun_8427139b99b9cd217f2e750a | UNDERPOWERED |
| sspec_b51d27525273a2d7b303e330 | trade_date_block_bootstrap | 11750 | BLOCKED | False | True | surrun_a26f36d36b151fb096d390b9 | UNDERPOWERED |
| sspec_1691b58a41a69cb8e3f69d49 | trade_date_block_bootstrap | 11751 | BLOCKED | False | True | surrun_9219e13e89ce4b6f4e22d148 | UNDERPOWERED |
| sspec_1691b58a41a69cb8e3f69d49 | trade_date_block_bootstrap | 11752 | BLOCKED | False | True | surrun_98611639fd38f85d0797231d | UNDERPOWERED |
| sspec_1691b58a41a69cb8e3f69d49 | trade_date_block_bootstrap | 11753 | BLOCKED | False | True | surrun_0941a7fb5e2480acd4dc8667 | UNDERPOWERED |
| sspec_129c4e401bd8ed5ea1955513 | trade_date_block_bootstrap | 11757 | BLOCKED | False | True | surrun_c64a0ef576c6ba6cb5b48903 | UNDERPOWERED |
| sspec_129c4e401bd8ed5ea1955513 | trade_date_block_bootstrap | 11758 | BLOCKED | False | True | surrun_1c7f9ecbe4aa00bbb4deb0aa | UNDERPOWERED |
| sspec_129c4e401bd8ed5ea1955513 | trade_date_block_bootstrap | 11759 | BLOCKED | False | True | surrun_7c041b44c9cb3aa1dc63caaf | UNDERPOWERED |
| sspec_8457b52fb12ffc506c5c268c | trade_date_block_bootstrap | 11760 | BLOCKED | False | True | surrun_11ed12056da5920a89b01f42 | UNDERPOWERED |
| sspec_8457b52fb12ffc506c5c268c | trade_date_block_bootstrap | 11761 | BLOCKED | False | True | surrun_fef3224c3679a6ca8cd423a5 | UNDERPOWERED |
| sspec_8457b52fb12ffc506c5c268c | trade_date_block_bootstrap | 11762 | BLOCKED | False | True | surrun_560fe6b8a6a56b755751b696 | UNDERPOWERED |
| sspec_6f50f372725077248326de08 | trade_date_block_bootstrap | 11763 | BLOCKED | False | True | surrun_87b66b7e66de322a42c62570 | UNDERPOWERED |
| sspec_6f50f372725077248326de08 | trade_date_block_bootstrap | 11764 | BLOCKED | False | True | surrun_f76317756972dd3b8aa7501c | UNDERPOWERED |
| sspec_6f50f372725077248326de08 | trade_date_block_bootstrap | 11765 | BLOCKED | False | True | surrun_82502124d5c72af49cb87c34 | UNDERPOWERED |
| sspec_d03c10259d8962fcd9c88d8c | trade_date_block_bootstrap | 11766 | BLOCKED | False | True | surrun_4c2eb5de358fb14b9a8b86b4 | UNDERPOWERED |
| sspec_d03c10259d8962fcd9c88d8c | trade_date_block_bootstrap | 11767 | BLOCKED | False | True | surrun_1a2a5d865219fa40684ee9c5 | UNDERPOWERED |
| sspec_d03c10259d8962fcd9c88d8c | trade_date_block_bootstrap | 11768 | BLOCKED | False | True | surrun_ceb8e5a6bcb232223411d649 | UNDERPOWERED |
| sspec_15cdf921185c6c5c92cc08ea | trade_date_block_bootstrap | 11769 | BLOCKED | False | True | surrun_e61cfe0f046793dce0111ae2 | UNDERPOWERED |
| sspec_15cdf921185c6c5c92cc08ea | trade_date_block_bootstrap | 11770 | BLOCKED | False | True | surrun_102fc310662d1b4a33db3910 | UNDERPOWERED |
| sspec_15cdf921185c6c5c92cc08ea | trade_date_block_bootstrap | 11771 | BLOCKED | False | True | surrun_6b813d147e4da8ef1bc589c4 | UNDERPOWERED |
| sspec_920ecdc185f4bcfac4c1034b | trade_date_block_bootstrap | 11772 | BLOCKED | False | True | surrun_6c5ada0e8e7f0f5221317f37 | UNDERPOWERED |
| sspec_920ecdc185f4bcfac4c1034b | trade_date_block_bootstrap | 11773 | BLOCKED | False | True | surrun_d5c8648475f36c57ee88d354 | UNDERPOWERED |
| sspec_920ecdc185f4bcfac4c1034b | trade_date_block_bootstrap | 11774 | BLOCKED | False | True | surrun_602951ab823f0dca75a4cbfe | UNDERPOWERED |
| sspec_d634d75a4167211ac0e4e1ad | trade_date_block_bootstrap | 11787 | BLOCKED | False | True | surrun_a3e0ce269d36f7ed953add65 | UNDERPOWERED |
| sspec_d634d75a4167211ac0e4e1ad | trade_date_block_bootstrap | 11788 | BLOCKED | False | True | surrun_dd531144fd96f4a4e62a3c37 | UNDERPOWERED |
| sspec_d634d75a4167211ac0e4e1ad | trade_date_block_bootstrap | 11789 | BLOCKED | False | True | surrun_2e7fc10250250cb6e74b1fd8 | UNDERPOWERED |
| sspec_916eb81b66236f6b0c878b8c | trade_date_block_bootstrap | 11790 | BLOCKED | False | True | surrun_2f61da00c38740808544eda8 | UNDERPOWERED |
| sspec_916eb81b66236f6b0c878b8c | trade_date_block_bootstrap | 11791 | BLOCKED | False | True | surrun_b3d91e7f1ce5ea131cb53d48 | UNDERPOWERED |
| sspec_916eb81b66236f6b0c878b8c | trade_date_block_bootstrap | 11792 | BLOCKED | False | True | surrun_34a870b42fe2d5ea93566a57 | UNDERPOWERED |
| sspec_297660383d7daa6b9894ba8d | trade_date_block_bootstrap | 11793 | BLOCKED | False | True | surrun_102ebcd2029e88add8a2b93f | UNDERPOWERED |
| sspec_297660383d7daa6b9894ba8d | trade_date_block_bootstrap | 11794 | BLOCKED | False | True | surrun_f2776d06ebb3b43c8c01fbf0 | UNDERPOWERED |
| sspec_297660383d7daa6b9894ba8d | trade_date_block_bootstrap | 11795 | BLOCKED | False | True | surrun_f81815b7bdaef081d40e987e | UNDERPOWERED |
| sspec_2ec6d059219c2609e5b4f9ee | trade_date_block_bootstrap | 11796 | BLOCKED | False | True | surrun_e0e7d5fff27a20fd917a1737 | UNDERPOWERED |
| sspec_2ec6d059219c2609e5b4f9ee | trade_date_block_bootstrap | 11797 | BLOCKED | False | True | surrun_228f07812b3377b4d04d90cc | UNDERPOWERED |
| sspec_2ec6d059219c2609e5b4f9ee | trade_date_block_bootstrap | 11798 | BLOCKED | False | True | surrun_3e44af9605c8a2851d5999de | UNDERPOWERED |
| sspec_1339b6ccd0c986f06cccb4ab | trade_date_block_bootstrap | 11799 | BLOCKED | False | True | surrun_54ca826c3263c18016f262ac | UNDERPOWERED |
| sspec_1339b6ccd0c986f06cccb4ab | trade_date_block_bootstrap | 11800 | BLOCKED | False | True | surrun_bc07f472fe585364ff68c084 | UNDERPOWERED |
| sspec_1339b6ccd0c986f06cccb4ab | trade_date_block_bootstrap | 11801 | BLOCKED | False | True | surrun_5a0aed16e723f1415f9d781a | UNDERPOWERED |
| sspec_7624adbe7f648eab89a8a3a8 | trade_date_block_bootstrap | 11802 | BLOCKED | False | True | surrun_3270f4f0f8d9b3d7720f2b33 | UNDERPOWERED |
| sspec_7624adbe7f648eab89a8a3a8 | trade_date_block_bootstrap | 11803 | BLOCKED | False | True | surrun_07566d992addfd536e2413b0 | UNDERPOWERED |
| sspec_7624adbe7f648eab89a8a3a8 | trade_date_block_bootstrap | 11804 | BLOCKED | False | True | surrun_4bb8674d741aad94f7c96b9b | UNDERPOWERED |
| sspec_487ba6544a769ba29031817d | trade_date_block_bootstrap | 11805 | BLOCKED | False | True | surrun_6b3853b65406ee9d0b378db3 | UNDERPOWERED |
| sspec_487ba6544a769ba29031817d | trade_date_block_bootstrap | 11806 | BLOCKED | False | True | surrun_633648bb737574800e5b8773 | UNDERPOWERED |
| sspec_487ba6544a769ba29031817d | trade_date_block_bootstrap | 11807 | BLOCKED | False | True | surrun_0c1806b965d7dd79d65ea0f6 | UNDERPOWERED |
| sspec_1d9845045f6c42cb331d1d1f | trade_date_block_bootstrap | 11808 | BLOCKED | False | True | surrun_7ca4ea5d7a73a71efc8dba5a | UNDERPOWERED |
| sspec_1d9845045f6c42cb331d1d1f | trade_date_block_bootstrap | 11809 | BLOCKED | False | True | surrun_b54a333044b3f9774d539b6b | UNDERPOWERED |
| sspec_1d9845045f6c42cb331d1d1f | trade_date_block_bootstrap | 11810 | BLOCKED | False | True | surrun_b1778309e024f68933c4c94b | UNDERPOWERED |
| sspec_49c83645a3956da01324f8ff | trade_date_block_bootstrap | 11817 | BLOCKED | False | True | surrun_77e4909062e6c52f55dee991 | UNDERPOWERED |
| sspec_49c83645a3956da01324f8ff | trade_date_block_bootstrap | 11818 | BLOCKED | False | True | surrun_f192fc51d34ec1d0624ea6be | UNDERPOWERED |
| sspec_49c83645a3956da01324f8ff | trade_date_block_bootstrap | 11819 | BLOCKED | False | True | surrun_ce30acafd1259d3bbf9d61c1 | UNDERPOWERED |
| sspec_4fe869acc6387192ce021e03 | trade_date_block_bootstrap | 11820 | BLOCKED | False | True | surrun_b46933b17ddb6df1be343916 | UNDERPOWERED |
| sspec_4fe869acc6387192ce021e03 | trade_date_block_bootstrap | 11821 | BLOCKED | False | True | surrun_22a5976790e36801299e253f | UNDERPOWERED |
| sspec_4fe869acc6387192ce021e03 | trade_date_block_bootstrap | 11822 | BLOCKED | False | True | surrun_a4a07364c56dcf4fe666860d | UNDERPOWERED |
| sspec_e5f39f8bb5a751cd64f3452a | trade_date_block_bootstrap | 11823 | BLOCKED | False | True | surrun_8c87a3805e29a61da87f69ad | UNDERPOWERED |
| sspec_e5f39f8bb5a751cd64f3452a | trade_date_block_bootstrap | 11824 | BLOCKED | False | True | surrun_ea1868ad1a7faf099005f002 | UNDERPOWERED |
| sspec_e5f39f8bb5a751cd64f3452a | trade_date_block_bootstrap | 11825 | BLOCKED | False | True | surrun_0d6a9f039dec9659b975f12e | UNDERPOWERED |
| sspec_bcb5b81c7b30afbc3c7d9494 | trade_date_block_bootstrap | 11826 | BLOCKED | False | True | surrun_199a87d8f04675daa7b64e60 | UNDERPOWERED |
| sspec_bcb5b81c7b30afbc3c7d9494 | trade_date_block_bootstrap | 11827 | BLOCKED | False | True | surrun_dc531e99f8874321bcec677c | UNDERPOWERED |
| sspec_bcb5b81c7b30afbc3c7d9494 | trade_date_block_bootstrap | 11828 | BLOCKED | False | True | surrun_f3d7bc55c40867b2bda7944c | UNDERPOWERED |
| sspec_816c3db399d5b746ca40a8c6 | trade_date_block_bootstrap | 11829 | BLOCKED | False | True | surrun_7336142e7679af2acd5455c5 | UNDERPOWERED |
| sspec_816c3db399d5b746ca40a8c6 | trade_date_block_bootstrap | 11830 | BLOCKED | False | True | surrun_0781c5feb75e61698edc1baa | UNDERPOWERED |
| sspec_816c3db399d5b746ca40a8c6 | trade_date_block_bootstrap | 11831 | BLOCKED | False | True | surrun_cd78f4fbcafad0d9ba48cdb5 | UNDERPOWERED |
| sspec_f0b31ad6cc243c23a11cbc42 | trade_date_block_bootstrap | 11832 | BLOCKED | False | True | surrun_c08c52f9c54f304dc588dbc1 | UNDERPOWERED |
| sspec_f0b31ad6cc243c23a11cbc42 | trade_date_block_bootstrap | 11833 | BLOCKED | False | True | surrun_61eecda803b85575f19cb6da | UNDERPOWERED |
| sspec_f0b31ad6cc243c23a11cbc42 | trade_date_block_bootstrap | 11834 | BLOCKED | False | True | surrun_b7052f05be67cdb5faa55066 | UNDERPOWERED |
| sspec_d851a40faead0b037d510433 | trade_date_block_bootstrap | 11835 | BLOCKED | False | True | surrun_f7dd71dda4ca340d8d21e923 | UNDERPOWERED |
| sspec_d851a40faead0b037d510433 | trade_date_block_bootstrap | 11836 | BLOCKED | False | True | surrun_c4ade899c307170386eadaed | UNDERPOWERED |
| sspec_d851a40faead0b037d510433 | trade_date_block_bootstrap | 11837 | BLOCKED | False | True | surrun_60c094353cfc5e54c7ff487f | UNDERPOWERED |
| sspec_78b41e38fc5036974930dc2b | trade_date_block_bootstrap | 11838 | BLOCKED | False | True | surrun_e55095c4b892d3c293167fed | UNDERPOWERED |
| sspec_78b41e38fc5036974930dc2b | trade_date_block_bootstrap | 11839 | BLOCKED | False | True | surrun_5db3993045bf751a0553940d | UNDERPOWERED |
| sspec_78b41e38fc5036974930dc2b | trade_date_block_bootstrap | 11840 | BLOCKED | False | True | surrun_9dc2e848ef798221cba9c5d3 | UNDERPOWERED |
| sspec_b180e11d1e420660f86a02e0 | trade_date_block_bootstrap | 11847 | BLOCKED | False | True | surrun_0d86bc0369e79376e0ee5fac | UNDERPOWERED |
| sspec_b180e11d1e420660f86a02e0 | trade_date_block_bootstrap | 11848 | BLOCKED | False | True | surrun_942f726c3a5a7160c4dee9a1 | UNDERPOWERED |
| sspec_b180e11d1e420660f86a02e0 | trade_date_block_bootstrap | 11849 | BLOCKED | False | True | surrun_5af4c1c7cdc24fecec6e0394 | UNDERPOWERED |
| sspec_aa37fa251597924ba486e04e | trade_date_block_bootstrap | 11850 | BLOCKED | False | True | surrun_9f097b9c505869c92e2023e5 | UNDERPOWERED |
| sspec_aa37fa251597924ba486e04e | trade_date_block_bootstrap | 11851 | BLOCKED | False | True | surrun_859378de0e8fecebb88ee7fd | UNDERPOWERED |
| sspec_aa37fa251597924ba486e04e | trade_date_block_bootstrap | 11852 | BLOCKED | False | True | surrun_32f6ab5b9538712f6b2ef460 | UNDERPOWERED |
| sspec_3103fd302018136f473f59ad | trade_date_block_bootstrap | 11853 | BLOCKED | False | True | surrun_7bf3fed8655d62ef45561db6 | UNDERPOWERED |
| sspec_3103fd302018136f473f59ad | trade_date_block_bootstrap | 11854 | BLOCKED | False | True | surrun_79facd1abe54259b76b47801 | UNDERPOWERED |
| sspec_3103fd302018136f473f59ad | trade_date_block_bootstrap | 11855 | BLOCKED | False | True | surrun_7e80621035da170511957a99 | UNDERPOWERED |
| sspec_5a1e6a6e03fbef7f18ad205b | trade_date_block_bootstrap | 11856 | BLOCKED | False | True | surrun_38f57dac7eca933d44fb2858 | UNDERPOWERED |
| sspec_5a1e6a6e03fbef7f18ad205b | trade_date_block_bootstrap | 11857 | BLOCKED | False | True | surrun_57916085953b3883c7a62cce | UNDERPOWERED |
| sspec_5a1e6a6e03fbef7f18ad205b | trade_date_block_bootstrap | 11858 | BLOCKED | False | True | surrun_0c825ebacf703bc69328cca1 | UNDERPOWERED |
| sspec_35010b26e525233351b67050 | trade_date_block_bootstrap | 11859 | BLOCKED | False | True | surrun_b602f75a62f2f8d80eb424bc | UNDERPOWERED |
| sspec_35010b26e525233351b67050 | trade_date_block_bootstrap | 11860 | BLOCKED | False | True | surrun_b63c310b3ca86d72c9edc342 | UNDERPOWERED |
| sspec_35010b26e525233351b67050 | trade_date_block_bootstrap | 11861 | BLOCKED | False | True | surrun_848e81d0660340bf8d4f5c43 | UNDERPOWERED |
| sspec_5337203aed1e7a74937ffda8 | trade_date_block_bootstrap | 11862 | BLOCKED | False | True | surrun_2bfa77d1d35bf14f761c78f0 | UNDERPOWERED |
| sspec_5337203aed1e7a74937ffda8 | trade_date_block_bootstrap | 11863 | BLOCKED | False | True | surrun_f9b6e9312ab174e9b001a73f | UNDERPOWERED |
| sspec_5337203aed1e7a74937ffda8 | trade_date_block_bootstrap | 11864 | BLOCKED | False | True | surrun_f1c1df0ae4cbaf76b73b4c61 | UNDERPOWERED |
| sspec_6686b645b2967f4de3521142 | trade_date_block_bootstrap | 11877 | BLOCKED | False | True | surrun_9fc68aac1c8c6dddbeb78d23 | UNDERPOWERED |
| sspec_6686b645b2967f4de3521142 | trade_date_block_bootstrap | 11878 | BLOCKED | False | True | surrun_e1f53a721ad4f25f350e9357 | UNDERPOWERED |
| sspec_6686b645b2967f4de3521142 | trade_date_block_bootstrap | 11879 | BLOCKED | False | True | surrun_9f46c4946f201531851a3dfc | UNDERPOWERED |
| sspec_8feca5b9413440472622c188 | trade_date_block_bootstrap | 11880 | BLOCKED | False | True | surrun_54f8164531dc3600c7bf9703 | UNDERPOWERED |
| sspec_8feca5b9413440472622c188 | trade_date_block_bootstrap | 11881 | BLOCKED | False | True | surrun_b8138721ef9e02235604ba2e | UNDERPOWERED |
| sspec_8feca5b9413440472622c188 | trade_date_block_bootstrap | 11882 | BLOCKED | False | True | surrun_44950473b2b36a0d4f5823ee | UNDERPOWERED |
| sspec_3e2b72e4787812cc88d2c3ed | trade_date_block_bootstrap | 11883 | BLOCKED | False | True | surrun_5f324853e70cb64b580306c3 | UNDERPOWERED |
| sspec_3e2b72e4787812cc88d2c3ed | trade_date_block_bootstrap | 11884 | BLOCKED | False | True | surrun_241f3ca9e1e00b0c936c674a | UNDERPOWERED |
| sspec_3e2b72e4787812cc88d2c3ed | trade_date_block_bootstrap | 11885 | BLOCKED | False | True | surrun_21c7c6e83ef7a4d88265f50e | UNDERPOWERED |
| sspec_1740cf32998cef05c858b97f | trade_date_block_bootstrap | 11886 | BLOCKED | False | True | surrun_1fe86cf373ac05e92ff6afb6 | UNDERPOWERED |
| sspec_1740cf32998cef05c858b97f | trade_date_block_bootstrap | 11887 | BLOCKED | False | True | surrun_8a39b57fd9d7519daa203085 | UNDERPOWERED |
| sspec_1740cf32998cef05c858b97f | trade_date_block_bootstrap | 11888 | BLOCKED | False | True | surrun_b1c4ef20bc303b5948b7df07 | UNDERPOWERED |
| sspec_14a33e7df4ef804e3016fcfd | trade_date_block_bootstrap | 11889 | BLOCKED | False | True | surrun_098abae4b541cfb19676c5c7 | UNDERPOWERED |
| sspec_14a33e7df4ef804e3016fcfd | trade_date_block_bootstrap | 11890 | BLOCKED | False | True | surrun_d22a1e05055e2b17822f0fa9 | UNDERPOWERED |
| sspec_14a33e7df4ef804e3016fcfd | trade_date_block_bootstrap | 11891 | BLOCKED | False | True | surrun_b0d4695232853340b4dab965 | UNDERPOWERED |
| sspec_428bd725758c549af88ecb4b | trade_date_block_bootstrap | 11892 | BLOCKED | False | True | surrun_51a7cfb3e164acdf4614a913 | UNDERPOWERED |
| sspec_428bd725758c549af88ecb4b | trade_date_block_bootstrap | 11893 | BLOCKED | False | True | surrun_2dbc95f5a8dc6d800db529b6 | UNDERPOWERED |
| sspec_428bd725758c549af88ecb4b | trade_date_block_bootstrap | 11894 | BLOCKED | False | True | surrun_483144998ae52c0e37ca889b | UNDERPOWERED |
| sspec_0598a6105897d79dca528b63 | trade_date_block_bootstrap | 11895 | BLOCKED | False | True | surrun_6a34de2297120221d0d014ce | UNDERPOWERED |
| sspec_0598a6105897d79dca528b63 | trade_date_block_bootstrap | 11896 | BLOCKED | False | True | surrun_fd87fed1721af3f0df094da2 | UNDERPOWERED |
| sspec_0598a6105897d79dca528b63 | trade_date_block_bootstrap | 11897 | BLOCKED | False | True | surrun_4466b7c96b4c151bfb225360 | UNDERPOWERED |
| sspec_aca34e15f8036aada065ceb4 | trade_date_block_bootstrap | 11898 | BLOCKED | False | True | surrun_bd6fb8b68466f50855d5e7b7 | UNDERPOWERED |
| sspec_aca34e15f8036aada065ceb4 | trade_date_block_bootstrap | 11899 | BLOCKED | False | True | surrun_4b11fc6f383a9ced9dc58b35 | UNDERPOWERED |
| sspec_aca34e15f8036aada065ceb4 | trade_date_block_bootstrap | 11900 | BLOCKED | False | True | surrun_ae3fbb82b738f748eb8a0da2 | UNDERPOWERED |
| sspec_61df4eeee7c7a28e77b295e3 | trade_date_block_bootstrap | 11901 | BLOCKED | False | True | surrun_cfe7865c9fdbf685432f9801 | UNDERPOWERED |
| sspec_61df4eeee7c7a28e77b295e3 | trade_date_block_bootstrap | 11902 | BLOCKED | False | True | surrun_0c932ca2327337cf868bc6b3 | UNDERPOWERED |
| sspec_61df4eeee7c7a28e77b295e3 | trade_date_block_bootstrap | 11903 | BLOCKED | False | True | surrun_b7bc903b5cf05db3edfcf74e | UNDERPOWERED |
| sspec_550bf30a5885a3fc12028e36 | trade_date_block_bootstrap | 11907 | BLOCKED | False | True | surrun_a7ecec32158d5da876892f83 | UNDERPOWERED |
| sspec_550bf30a5885a3fc12028e36 | trade_date_block_bootstrap | 11908 | BLOCKED | False | True | surrun_999b6bfbd970b4c0e422cade | UNDERPOWERED |
| sspec_550bf30a5885a3fc12028e36 | trade_date_block_bootstrap | 11909 | BLOCKED | False | True | surrun_8242b56815a20b67e11f32da | UNDERPOWERED |
| sspec_49351d952c375e7a2f88303d | trade_date_block_bootstrap | 11910 | BLOCKED | False | True | surrun_e5531bfae9880c6aeb1def3c | UNDERPOWERED |
| sspec_49351d952c375e7a2f88303d | trade_date_block_bootstrap | 11911 | BLOCKED | False | True | surrun_c599d63e0bd190a0c53f347d | UNDERPOWERED |
| sspec_49351d952c375e7a2f88303d | trade_date_block_bootstrap | 11912 | BLOCKED | False | True | surrun_71d84b7d0e48a1f9ad5b7ead | UNDERPOWERED |
| sspec_fb980ba3ffcf6d4f5495ea0b | trade_date_block_bootstrap | 11913 | BLOCKED | False | True | surrun_7ec8a184a4568592865485d2 | UNDERPOWERED |
| sspec_fb980ba3ffcf6d4f5495ea0b | trade_date_block_bootstrap | 11914 | BLOCKED | False | True | surrun_b1eaa9c79f65c0db2c3d9e11 | UNDERPOWERED |
| sspec_fb980ba3ffcf6d4f5495ea0b | trade_date_block_bootstrap | 11915 | BLOCKED | False | True | surrun_b46fd70e625ff38a73e6de99 | UNDERPOWERED |
| sspec_22c1ae4e27e920d5fc0aedd1 | trade_date_block_bootstrap | 11916 | BLOCKED | False | True | surrun_cf6adad5259ebcebccfdd125 | UNDERPOWERED |
| sspec_22c1ae4e27e920d5fc0aedd1 | trade_date_block_bootstrap | 11917 | BLOCKED | False | True | surrun_0d01c68e19691247656fdb4c | UNDERPOWERED |
| sspec_22c1ae4e27e920d5fc0aedd1 | trade_date_block_bootstrap | 11918 | BLOCKED | False | True | surrun_94c258106d304c4681b8cb8d | UNDERPOWERED |
| sspec_0b74115585bdeef812d6570f | trade_date_block_bootstrap | 11919 | BLOCKED | False | True | surrun_1d83c96c424f225f8f3d3c26 | UNDERPOWERED |
| sspec_0b74115585bdeef812d6570f | trade_date_block_bootstrap | 11920 | BLOCKED | False | True | surrun_db428242d952653c53d2d0d5 | UNDERPOWERED |
| sspec_0b74115585bdeef812d6570f | trade_date_block_bootstrap | 11921 | BLOCKED | False | True | surrun_524560515a6a1f9a171d35a8 | UNDERPOWERED |
| sspec_9cf519546f2d649906291e5b | trade_date_block_bootstrap | 11922 | BLOCKED | False | True | surrun_566deec33448f18150b45c61 | UNDERPOWERED |
| sspec_9cf519546f2d649906291e5b | trade_date_block_bootstrap | 11923 | BLOCKED | False | True | surrun_761f0a288fdfd1a0561a55c1 | UNDERPOWERED |
| sspec_9cf519546f2d649906291e5b | trade_date_block_bootstrap | 11924 | BLOCKED | False | True | surrun_c98c91250456d6bff3963296 | UNDERPOWERED |
| sspec_16dbaeb5cc9f96b689f3651e | trade_date_block_bootstrap | 11925 | BLOCKED | False | True | surrun_1e40cdf87df57211e4daacc0 | UNDERPOWERED |
| sspec_16dbaeb5cc9f96b689f3651e | trade_date_block_bootstrap | 11926 | BLOCKED | False | True | surrun_4243b3d7c15f215013ea307c | UNDERPOWERED |
| sspec_16dbaeb5cc9f96b689f3651e | trade_date_block_bootstrap | 11927 | BLOCKED | False | True | surrun_1218f06c47ca94cf215703e1 | UNDERPOWERED |
| sspec_adce3f052100b7b14fc97ff9 | trade_date_block_bootstrap | 11928 | BLOCKED | False | True | surrun_f17b8bf533dff86e0769c1d7 | UNDERPOWERED |
| sspec_adce3f052100b7b14fc97ff9 | trade_date_block_bootstrap | 11929 | BLOCKED | False | True | surrun_27dae7c9eba9899063ce8528 | UNDERPOWERED |
| sspec_adce3f052100b7b14fc97ff9 | trade_date_block_bootstrap | 11930 | BLOCKED | False | True | surrun_ae9409e9bd37ce97f6fc812d | UNDERPOWERED |
| sspec_d57bd0277f061a202fe1884e | trade_date_block_bootstrap | 11937 | BLOCKED | False | True | surrun_e0b559d7a104feaaa84c6585 | UNDERPOWERED |
| sspec_d57bd0277f061a202fe1884e | trade_date_block_bootstrap | 11938 | BLOCKED | False | True | surrun_f019d16830c2c6067b5b5447 | UNDERPOWERED |
| sspec_d57bd0277f061a202fe1884e | trade_date_block_bootstrap | 11939 | BLOCKED | False | True | surrun_2a6204b040ca361701ac8b4d | UNDERPOWERED |

## Machinery Inventory

- `SurrogateStudyRun` schema and deterministic serialization live in `src/alpha_system/governance/surrogate_run.py`.
- `surrogate_flag` is threaded through `TrialLedgerRecord`; true surrogate trials are excluded from production variant/family counts.
- `alpha governance surrogate-calibrate` runs seeded surrogate calibrations in caller-supplied isolated namespaces.
- Real-data calibration over the kill-shot StudySpec remains a coordinator runbook step before FUTSUB-P28 kill-shot resume.
