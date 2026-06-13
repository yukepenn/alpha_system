# Real-Data Surrogate Calibration: sspec_dec89a327a9c50957adca780

This coordinator report is value-free: it records ids, run counts, seeds, gate outcomes, and the declared threshold only. It contains no label, feature, return, diagnostic, signal, or cost values.

## Scope

- Declared K per perturbation config: 3
- Bound statement: zero passes in K bounds false-pass rate at about 3/K at 95%.
- Declared primary horizon used for this run: `5m`.
- Perturbation configs: trade_date_block_shuffle, trade_date_block_bootstrap.
- Runtime factor derivation path: `alpha_system.governance.surrogate_run.study_config_for_surrogate_scope` -> `StudyConfig.from_mapping`.
- Declared feature family: `regime_volatility_compression`.
- Declared factor count: 5.
- Declared factors: `base_ohlcv_trendiness`, `base_ohlcv_atr`, `liquidity_structure_range_contraction`, `base_ohlcv_rolling_range`, `base_ohlcv_returns`.
- Excluded all-null factor partitions: 0.
- Declared label pack count: 24.
- Declared label versions: `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a`, `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e`, `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64`, `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a`, `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9`, `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022`, `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb`, `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3`, `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b`, `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031`, `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6`, `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2`, `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b`, `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742`, `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57`, `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce`, `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da`, `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515`, `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0`, `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a`, `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b`, `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276`, `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce`, `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b`.
- Staged surrogate sub-config count: 120.
- Off-grid locked label event_ts count: 0.
- Isolated namespace: `/home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_v5_regime_dec89a`.

## Staging Provenance

| Factor | Runtime Factor | Feature Version | Label Version | Feature Partition | Label Partition | Feature Rows | Label Rows | Off-Grid Label event_ts |
|---|---|---|---|---|---|---:|---:|---:|
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_f1c2779d7547239ae6ff34481e01ac944070e42dd7a7e8df6240fea10d4e0f19` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/1747660 | 341120/341120 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_a3085f71761d4bbcf725d1a398638059ef7a94f51bc6f3d02668f69443403862` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/1747660 | 341120/341120 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_b4a1c004a5039435a990f9933e6ab92ec2e90419b77dc6b211fc6528bc798d14` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/1747660 | 341120/341120 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_8eadbbf78450fc563380dad80469abc3cff4cc5446c0d022cdc8129cb0c96cea` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/1747660 | 341120/341120 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_33907b24924fe90263dad2c42de580d41c920b9bfaa1bda7f2cad45792d17a9f` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/1747660 | 341120/341120 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_74a10e20262d70407612c3a32900f8e571bfc9feef82080af0ae4d830a22dc20` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/1748040 | 341115/341115 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_fb274848e902550ed5b5b9bae9173479df98503700c6f718a535343db57dc425` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/1748040 | 341115/341115 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_42bfbf5d66248b2d51a94fcc1361b9bb0c14282ee3f23b4b9028466fcfbaba96` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/1748040 | 341115/341115 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_c3cb280739705e10c5492c39effb49cf48de1df3478839a76da7f85efdad810b` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/1748040 | 341115/341115 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_9d7188f27540f44dab8f60407b290f3cf4c84b49bfe305921b111c0b119d9a3e` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/1748040 | 341115/341115 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_a19b1bb2c5b63d9a0f80e65225dec7de59c5fe3605f8f310c3f5ff354113f8d4` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/1766815 | 345881/345881 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_6687c6ae47f3930931a7da2a855f058c0416d286a2f5529591831ae19ac37cd7` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/1766815 | 345881/345881 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_cd9b0e5f6dbed0acae572d1ce7f3a8ab0be9e2d380c013da675218ddbf5675fb` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/1766815 | 345881/345881 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_bb27b5c664ca30b57ea37816da25dcab972d7b6f495f3741cf907a982f360ca6` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/1766815 | 345881/345881 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_69c93747723d6bfa9b1676be7a3219f27dcc4803c2671bb67884596dab510d15` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/1766815 | 345881/345881 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_226faee503679b9bf0bc0af424cff89c463de90526b2ebd111fb70328e705537` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/1770595 | 347293/347293 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_1dc93b95fd7bf6035605afe5dcb8330b80bb9887aef0f5b1ec14141f7b6749c2` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/1770595 | 347293/347293 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_9d4690db28e9f738e771dc94c48ed5328761343aba8049715b5c08aa36ffb682` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/1770595 | 347293/347293 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_1a06d7a438c56b2633021598512d31ff0f728f2a9f8530f43b248f9738156968` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/1770595 | 347293/347293 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_7257bfbbef9b638d6bd8a0cf522c171ce9a3451b9a4708c19df96853845e871a` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/1770595 | 347293/347293 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_cffddb084b1cb88a8a80875038da85f770b8ce3095be706ef8838f95f7f90a8b` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/1765765 | 346064/346064 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_098e9f7336b384a6226076afb107fcc863db44854a0dd6867b87fb0cec983ee1` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/1765765 | 346064/346064 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_ba13123dbc2ec0e8eaa4116166875abca527bf4fde307eb05672374ecd779dee` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/1765765 | 346064/346064 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_df2e186c7f46a1024713006379862d8299bdb3a160cdeef6a6c281fa60daae33` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/1765765 | 346064/346064 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_9ae6640662c19c8e5847115438acc2185ef2a2af393c056b6c21e782c028eceb` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/1765765 | 346064/346064 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_8a2d3cd3e4b6b9fc1749a1ddcc89d395d0ead379e7d3c8416a52330915006faa` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/1734290 | 339866/339866 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_6cdc34d2b4e1694d83d1f7fc9f8cbafaab3f2c3d95ea189405a34fdc6044aa60` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/1734290 | 339866/339866 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_dee577ace9ba10c97a7cc49196d76eed484ce31e18848c91b623be2aff338f6f` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/1734290 | 339866/339866 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_d2b88c50e5fdd7e9437ac04b756fff55de63bd56a16ceab886e563a950c21e6a` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/1734290 | 339866/339866 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_a9b2d9a7c7bfec8081327a0d8fab67ec5db80b66cd33a67acd8e8041b8061ad8` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/1734290 | 339866/339866 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_4602b3b23df701f39074f069ce9fb495e5e446ca5933c8d2ab1076041ab69dd6` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/1722805 | 337734/337734 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_cdb79d11961f79be454db14c15c7219af4f4a018998d25de520263c81d13f0d1` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/1722805 | 337734/337734 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_59992f1e694efa7bfb2fa95c8f377c519373a81b6e4ea7f4def999b02411da2b` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/1722805 | 337734/337734 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_265fbe4b5fb41600e178287b6bc32450fd94759fa7572d1b7edaa806be7b29d9` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/1722805 | 337734/337734 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_003e2dc40d41cb1ab2733eb1342a3e384be76fce7dbae95edd96f3d88b4c928c` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/1722805 | 337734/337734 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_e19f1f6873a10112d83c82c6b22590e798a35b23e6b6b40694dfc6421bfff5e4` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/703195 | 138748/138748 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_2b42c21c4a87171fb792b334664ae06687f3d2f3f7f376e8e3aec61e77ca7062` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/703195 | 138748/138748 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_415aa929e6668122a1dfa8f5248140acba6c9f1403e0d476201e17aa52679cad` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/703195 | 138748/138748 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_7b24d9a1fca29032535ab66c825acc70cd7c09b22e1be4b7f9f7c8065cfef7c1` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/703195 | 138748/138748 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_0efe6b887d655c4c42d3b062f9b5db120cf16aeb8fe785b3e2ab879a91e7a732` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/703195 | 138748/138748 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_6d9794214b357fc64c9bc3dc5ca86bf910136c8dc1910bbcba78dfc77046b2cc` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/1749225 | 341715/341715 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_cc359728cd8a0a7296ec83722954152f525ea3406db219496ae26327d275f3b3` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/1749225 | 341715/341715 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_edf0e8b8207df8f1f207d3ac2e6a13e4279565bdcda47454b55683b50092e7e0` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/1749225 | 341715/341715 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_914a59404c258852874c059048bbfaf6daf604dcf120b0de8ca8caab9dab0ec1` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/1749225 | 341715/341715 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_52e28c5d3c5418d28d341fdef27cbb5336dea37f6069b04f9b911c033fffa870` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/1749225 | 341715/341715 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_0fb077644f319fd39fe40f95f1ae4d6b22115e4becc806e581562cbbaeb7e45f` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/1744645 | 340507/340507 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_a7572a52f6351008df61e0c7b638879c9787ba0fd38c4ed7540b3440846404a1` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/1744645 | 340507/340507 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_a124aad0f40c93667a7f9daf327da4b30c81038b92033d4565df11bd32f64b2f` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/1744645 | 340507/340507 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_2440f03222a90e8547cbf2b3dba5e33a44d670faddc44874bd29b4c7e6235d12` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/1744645 | 340507/340507 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_59fdb2b0a1a8ad1529649cf4385e33cbed091f4a8a57373a9cf10fc5c8914c49` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/1744645 | 340507/340507 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_b736de68b8684cf1dbaebc2108defe1df590e6f8dd33dac25700908880246ad4` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/1766965 | 345938/345938 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_0d6560c41a442a34c5424ea2c19a25dfdb36eb5dda7d34a2907a9c96866e972a` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/1766965 | 345938/345938 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_1db37f6c98e32b7974988ddea62a93d924bb65421f0c74e78e1f353ff6957628` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/1766965 | 345938/345938 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_2dd96bb58b74167b6d1dfaf782603dbeef5850cc3c98c7fe5352e4748b161dec` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/1766965 | 345938/345938 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_f15b6e711e666ee25dbfd4f67960176e6534b6a35f54d85a30d20242f92f7e91` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/1766965 | 345938/345938 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_4c59131fbe62d38d3c6e530e4474cf595694874662b730dde889a52636c9a46b` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/1770560 | 347280/347280 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_746e5da584cc75d1a8b340fd26acee64bc3c4bd5218cb0332f4770364f3d699e` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/1770560 | 347280/347280 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_5e4161cf763ffa468d5bee2feb46b2cecbbd8dadd4288db6ec7523f4a5c2bc3f` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/1770560 | 347280/347280 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_3a66218f1a31f945c9c45eb97b317584f0df4af3894c3263d36560144bfe59bc` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/1770560 | 347280/347280 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_5daa14b29630c57037e18d286ef5788d3588ac57c9a7b8fe1d74b86fe58ef73b` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/1770560 | 347280/347280 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_eacffee77c13955cb9e9674d544010f48ba3ef9dcc53aa6143dcdc5e81ca9fd2` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/1766790 | 346469/346469 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_0b3141650580ea14ad0e5741a9d6c4c350b49fecc9076df8480160fa4ad748e3` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/1766790 | 346469/346469 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_9acb6ca1dc94f4ea906fa1f3ff858c81b7f4927163575b005cd900b0d739694a` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/1766790 | 346469/346469 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_f7a9c8ed2cbb4217306a1f56b99cc6e48099f07b04f97afe936fe848281e4662` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/1766790 | 346469/346469 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_c2e1bd61f2f6f627eeddedd85c9eee5b1e889532fbf70f59d1e50ed4126eb09f` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/1766790 | 346469/346469 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_cf59eed2332c748308cbd0f656e911a701eb3c644acf8e6e9d9d14518fd3978e` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/1734960 | 340126/340126 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_bff0c4659b8cdc5265e32c97b8cc04a4315395b2ad6bacd27837811616e2f9b6` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/1734960 | 340126/340126 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_d57b1960be9745d59c85564da8f9ed59a8d83982dc8e739f22eddc5da19de56d` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/1734960 | 340126/340126 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_4f78f4f2ca92f27eb573c2ba6948e90d90be3b83750c223339df3d8ee969262c` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/1734960 | 340126/340126 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_7be90cc648e513434ea41e0f0afb0dbdb5319b9cac720e3e433a7aaca8a980dd` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/1734960 | 340126/340126 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_ca00e08b53bfd25e1428f1afd6994749cec39b23ba30aadd90efe0389ba7bbf0` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/1722645 | 337672/337672 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_a7bffaaa26b8cd679c9ce52957b7f220d97f3962909d88dac08cb0cdd576f69d` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/1722645 | 337672/337672 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_f05ae8141eaa6da6a639baf615a22b2beb21067dd2a37ce48e0467cf07a676e3` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/1722645 | 337672/337672 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_221f386f18a622efe6a9985e85a65cb7fb724b62b8200e9e4754b48553c49613` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/1722645 | 337672/337672 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_7a9f839bc61a4dc663462104f0ac01f0d7c5ff658216b3ed3ab73b71c79d56c3` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/1722645 | 337672/337672 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_d818357b43578c9d65c11606723adb3e151bace39ec3cd740de959d057995b8a` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/703050 | 138694/138694 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_f34beacb9ee5d750a2bb6af74f0f55934fe27123955a6d82d8e3e810fa7b4e9d` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/703050 | 138694/138694 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_c854cce58f51a8680cb1c26f5c558f926560a6190c737ce4e96ee9cf92fdb1ad` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/703050 | 138694/138694 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_71ab9ce697100c13ee08434a4967aef43e475df0f3f37a6fcb47caed6050bc8c` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/703050 | 138694/138694 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_ed71c098de04f0278c26f1eca949664c641469d280787b9f675c59c3af7aac40` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/703050 | 138694/138694 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_6906625af6a7aef089178eb9f4075c2f020b4dadca31e1b458a180d81c9cb486` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/1644205 | 305433/305433 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_217d8ea3ae3be157436579c9056cbec31ddaaa2786511bd51f2a73cb8dbee09c` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/1644205 | 305433/305433 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_b700ea18d3300d099c704a46efd0b208d27bd11015474985e86797b8f3956d39` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/1644205 | 305433/305433 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_2ebd3206e7f527db6f373992585d67fcf594d7b2391436576d56ebb433994591` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/1644205 | 305433/305433 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_b82ef680c3489a8c5293550ceecba577f0b42bace3dc02abf415799c6831dd98` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/1644205 | 305433/305433 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_20950b3a1c1a980a9c7dac3e77eb4728dbc3320f3244004617f623ccf2e71b67` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/1690425 | 322373/322373 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_9f95dfa95a859544818003386d0c811b701074c4825f03db096597d43317c923` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/1690425 | 322373/322373 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_00c564b9c7c394d7a45d956a01e9fd551c56dacd2d0aaa1cc63f6bcce0cef8f6` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/1690425 | 322373/322373 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_0098e1e4b8839a68ba1bd55a0bfc4214e39ba18a27e668ba35db9fba5a079346` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/1690425 | 322373/322373 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_1b560bc4ef182214f49a6f5f0f128e89b0febed0d101deef3c866b82775cdac9` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/1690425 | 322373/322373 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_bb415d8ebe51a5428842d5f2842c04d3786c876bcd052939a6a13876997468b5` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/1699475 | 322315/322315 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_0421c238a447060bd26f1e5831d5583f3870337afffb5b94e796d3051c7d8e0a` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/1699475 | 322315/322315 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_1b55fd6420915f6cc6050290eaef01aafea3d372a5669bf65f2b8b48be3a866b` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/1699475 | 322315/322315 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_1625f547afdafce94be491e00714e479dbcf7a0d3246e160d890b12e3acbbf09` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/1699475 | 322315/322315 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_bba78e8dd1aaf7703cd95cc3b5254d2b32920702be8cd899addd046610c8b8ad` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/1699475 | 322315/322315 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_2b5be082aaaf85050785cf1ef6e6bd7c9c41a080b35c2e9f6a076348b867497d` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/1725810 | 331308/331308 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_9be03014e8841575e24919c497b001d26a45bcd78d44b3b91a22478073f59bf0` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/1725810 | 331308/331308 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_540151af47fe7e52ab47052f8f015be8d8d495c160493147e5bd983832eaa4c4` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/1725810 | 331308/331308 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_d394d33dd4d9b982f6fbfc4392383e914c87e376d563b615325d5f30c0f15846` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/1725810 | 331308/331308 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_024659f49970036b3ae401df727657e89d85b670b13645f1e36f08f2b84f971d` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/1725810 | 331308/331308 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_ae52c79f634bc29974cfb1582522cc5bb710326fbdb6af581f1dd24405ccc460` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/1712180 | 327109/327109 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_f5f751c1b25087d8473acd4e16f29d6714c73efcd378e67a5d89cbb6e83a08b1` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/1712180 | 327109/327109 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_0d1ee363360420a067e9a67d9ea0a788ee4a7d1b0792ecd5b78ebcdbbe5b5fa0` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/1712180 | 327109/327109 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_77854c7e5938beefb69574fb6169b14b5cdb1539666819404a01b22f74aa9a02` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/1712180 | 327109/327109 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_e258f70571883e7bcb35c7b2fa3ba65c2e11e9e5e37e7c52791c56c828aff9f8` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/1712180 | 327109/327109 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_a4a3b0a29b98f8c8dad027b6831a224104b5f725639879e42219765ea03791d6` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/1667700 | 317000/317000 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_dcda9c766aeea6cf7019ffc771a15f221dd1bd62a63e42ba00c9716a2dff7d0b` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/1667700 | 317000/317000 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_3d037bdd6bd19eaead26757d705e713859ab3b09b59776903a9251bedad8ef59` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/1667700 | 317000/317000 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_d02785b69c8f0e46c72f9d107998653bdf7d8d4864268a4d21733f690bb0861d` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/1667700 | 317000/317000 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_306d6f0ef2d8cba679d5bf88aaae1df5d8df66f24f1a0140ac8d089cd58123fb` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/1667700 | 317000/317000 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_2660fe9b1d98cedb9672183b08e667b206f311f720462c975c2bda03504e4064` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/1667785 | 318544/318544 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_23b2d3b5a4143460aae1bf690cda9c8d612f8059e4dbd074e32409a33f39e59c` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/1667785 | 318544/318544 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_b5267b01c8e49cd8f720f7b1448f36010ce2ce80575e756fb49c73616a594c56` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/1667785 | 318544/318544 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_9f70717700603634bc6f8d0cc1d8ad51751f87085ed6b31b887c97e029128047` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/1667785 | 318544/318544 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_c7d28c609108c388468f46d014c3ad92fee6fd3c121a94477566019f2ce3420c` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/1667785 | 318544/318544 | 0 |
| `base_ohlcv_trendiness` | `base_ohlcv_trendiness` | `fver_bfb61c493874444428bde917fe0be501f34dd3c1d4096a6d78f9735843c5f7b3` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/692965 | 134990/134990 | 0 |
| `base_ohlcv_atr` | `base_ohlcv_atr` | `fver_bf666b2cedc53dbda076beb6720dd846772c23a46df736ca54c7452e87cd3871` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/692965 | 134990/134990 | 0 |
| `liquidity_structure_range_contraction` | `liquidity_structure_range_contraction` | `fver_83a9ebcc5aa260b2c242c8c5dce6dadf053c7bdb698b4c25820a286680f2a95c` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/692965 | 134990/134990 | 0 |
| `base_ohlcv_rolling_range` | `base_ohlcv_rolling_range` | `fver_c54a5e5995e6f5fc1408ccc263ab212925395bf87ce053f7aae785562270fc3f` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/692965 | 134990/134990 | 0 |
| `base_ohlcv_returns` | `base_ohlcv_returns` | `fver_225c5e88a3f7e1a33701677c863c9f1283c09721b18672cdd158b01a9adbba8d` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/692965 | 134990/134990 | 0 |

## excluded_factors

- None.

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

- Run count: 720
- Error count: 0
- Statistic pass count: 0
- Statistic pass rate: 0.000000
- Eligibility clean count: 720

## Per-Perturbation Counts

| Perturbation | Runs | Errors | Statistic Passes | Eligibility Clean | Statistic Pass Rate | Verdict |
|---|---:|---:|---:|---:|---:|---|
| trade_date_block_bootstrap | 360 | 0 | 0 | 360 | 0.000000 | zero-pass-met |
| trade_date_block_shuffle | 360 | 0 | 0 | 360 | 0.000000 | zero-pass-met |

## Per-Run Seeds And Outcomes

| StudySpec | Perturbation | Seed | Outcome | Statistic Passed | Eligibility Clean | Surrogate ID | Reason |
|---|---|---:|---|---|---|---|---|
| sspec_7e79f1b5e4854cb1257cda63 | trade_date_block_shuffle | 9600 | BLOCKED | False | True | surrun_aa1a4a6456010959ac8bf322 | UNDERPOWERED |
| sspec_7e79f1b5e4854cb1257cda63 | trade_date_block_shuffle | 9601 | BLOCKED | False | True | surrun_2b20c5ffcd00ed6420ebae6d | UNDERPOWERED |
| sspec_7e79f1b5e4854cb1257cda63 | trade_date_block_shuffle | 9602 | BLOCKED | False | True | surrun_001582fe90180ec5d991edc4 | UNDERPOWERED |
| sspec_1ad21ea07e54b70a3c22ca54 | trade_date_block_shuffle | 9603 | BLOCKED | False | True | surrun_45e88ce75919129aac19d882 | UNDERPOWERED |
| sspec_1ad21ea07e54b70a3c22ca54 | trade_date_block_shuffle | 9604 | BLOCKED | False | True | surrun_3168c4d270b2b806a2ef665c | UNDERPOWERED |
| sspec_1ad21ea07e54b70a3c22ca54 | trade_date_block_shuffle | 9605 | BLOCKED | False | True | surrun_1301740aa59441a2951f7119 | UNDERPOWERED |
| sspec_93ae072de5e1947d33a9d0dc | trade_date_block_shuffle | 9606 | BLOCKED | False | True | surrun_421dc06113faa6ddd0c6672a | UNDERPOWERED |
| sspec_93ae072de5e1947d33a9d0dc | trade_date_block_shuffle | 9607 | BLOCKED | False | True | surrun_2ba3ba6969697b9f44e6992f | UNDERPOWERED |
| sspec_93ae072de5e1947d33a9d0dc | trade_date_block_shuffle | 9608 | BLOCKED | False | True | surrun_1b00ab82b2b73d718e72ac0c | UNDERPOWERED |
| sspec_f55b84e46d44016a0ead37fd | trade_date_block_shuffle | 9609 | BLOCKED | False | True | surrun_96d785984c5c61a643334546 | UNDERPOWERED |
| sspec_f55b84e46d44016a0ead37fd | trade_date_block_shuffle | 9610 | BLOCKED | False | True | surrun_9b1c9505dd5eb5593975e584 | UNDERPOWERED |
| sspec_f55b84e46d44016a0ead37fd | trade_date_block_shuffle | 9611 | BLOCKED | False | True | surrun_7e89965547a359f94994f2f4 | UNDERPOWERED |
| sspec_8998644a516c93a24b3ef787 | trade_date_block_shuffle | 9612 | BLOCKED | False | True | surrun_4516331b150ab421f129481f | UNDERPOWERED |
| sspec_8998644a516c93a24b3ef787 | trade_date_block_shuffle | 9613 | BLOCKED | False | True | surrun_717139966d5929b2404dcaab | UNDERPOWERED |
| sspec_8998644a516c93a24b3ef787 | trade_date_block_shuffle | 9614 | BLOCKED | False | True | surrun_f839af353f4ce622d7ef29c9 | UNDERPOWERED |
| sspec_3d8d87ebd27287fe2aac314a | trade_date_block_shuffle | 9615 | BLOCKED | False | True | surrun_a14b01e5e27c0709334ad1ce | UNDERPOWERED |
| sspec_3d8d87ebd27287fe2aac314a | trade_date_block_shuffle | 9616 | BLOCKED | False | True | surrun_08d528226f374eba34a63df8 | UNDERPOWERED |
| sspec_3d8d87ebd27287fe2aac314a | trade_date_block_shuffle | 9617 | BLOCKED | False | True | surrun_4d7e9aa50c0a3531b3f1cbbe | UNDERPOWERED |
| sspec_7e25b1b59f9442607d51c9b0 | trade_date_block_shuffle | 9618 | BLOCKED | False | True | surrun_154ecfa7073eb512767055ae | UNDERPOWERED |
| sspec_7e25b1b59f9442607d51c9b0 | trade_date_block_shuffle | 9619 | BLOCKED | False | True | surrun_df2d4837edbf422895ee2757 | UNDERPOWERED |
| sspec_7e25b1b59f9442607d51c9b0 | trade_date_block_shuffle | 9620 | BLOCKED | False | True | surrun_eb2974f5cad346be7862ce39 | UNDERPOWERED |
| sspec_1a30430408744f9767cadb44 | trade_date_block_shuffle | 9621 | BLOCKED | False | True | surrun_8ca4f77d3a617f1017efa0b2 | UNDERPOWERED |
| sspec_1a30430408744f9767cadb44 | trade_date_block_shuffle | 9622 | BLOCKED | False | True | surrun_41d5bdf99d45325230f68edb | UNDERPOWERED |
| sspec_1a30430408744f9767cadb44 | trade_date_block_shuffle | 9623 | BLOCKED | False | True | surrun_3988000140e2759a9fc13b7a | UNDERPOWERED |
| sspec_ffb23ccd6863fdef6033a724 | trade_date_block_shuffle | 9624 | BLOCKED | False | True | surrun_12e9e31691af2e98c11654dd | UNDERPOWERED |
| sspec_ffb23ccd6863fdef6033a724 | trade_date_block_shuffle | 9625 | BLOCKED | False | True | surrun_8324229dc7ff6ed503ed29c7 | UNDERPOWERED |
| sspec_ffb23ccd6863fdef6033a724 | trade_date_block_shuffle | 9626 | BLOCKED | False | True | surrun_86c34069a7dc6d851dd0cae2 | UNDERPOWERED |
| sspec_8a4da6ebf51436aa38ad6907 | trade_date_block_shuffle | 9627 | BLOCKED | False | True | surrun_910bb03f4f4f6e64ea3b906d | UNDERPOWERED |
| sspec_8a4da6ebf51436aa38ad6907 | trade_date_block_shuffle | 9628 | BLOCKED | False | True | surrun_8af9ab92ab4560563d402de3 | UNDERPOWERED |
| sspec_8a4da6ebf51436aa38ad6907 | trade_date_block_shuffle | 9629 | BLOCKED | False | True | surrun_988d58938a97a03f7768bb4b | UNDERPOWERED |
| sspec_a717397d0e0a7cb384b5b956 | trade_date_block_shuffle | 9630 | BLOCKED | False | True | surrun_d47703e495de38f2cb4428d1 | UNDERPOWERED |
| sspec_a717397d0e0a7cb384b5b956 | trade_date_block_shuffle | 9631 | BLOCKED | False | True | surrun_fa3a46b64f09503834b31427 | UNDERPOWERED |
| sspec_a717397d0e0a7cb384b5b956 | trade_date_block_shuffle | 9632 | BLOCKED | False | True | surrun_6f5393806c9fadf4d155281c | UNDERPOWERED |
| sspec_cb719518b6985d25d6ccd08c | trade_date_block_shuffle | 9633 | BLOCKED | False | True | surrun_29956ecce519386b1f052fd3 | UNDERPOWERED |
| sspec_cb719518b6985d25d6ccd08c | trade_date_block_shuffle | 9634 | BLOCKED | False | True | surrun_c9ad668d5ad79c751c611de1 | UNDERPOWERED |
| sspec_cb719518b6985d25d6ccd08c | trade_date_block_shuffle | 9635 | BLOCKED | False | True | surrun_b550cffda5fde2677747ffac | UNDERPOWERED |
| sspec_8dd3be627defa4bdbd9d86ec | trade_date_block_shuffle | 9636 | BLOCKED | False | True | surrun_85290c904d5d2a7ab1ffcff5 | UNDERPOWERED |
| sspec_8dd3be627defa4bdbd9d86ec | trade_date_block_shuffle | 9637 | BLOCKED | False | True | surrun_53944145233b38f7c933f623 | UNDERPOWERED |
| sspec_8dd3be627defa4bdbd9d86ec | trade_date_block_shuffle | 9638 | BLOCKED | False | True | surrun_ace647fb00b70d18e4bfb7a9 | UNDERPOWERED |
| sspec_520f127a1734d90457cd4442 | trade_date_block_shuffle | 9639 | BLOCKED | False | True | surrun_e650352aac3e31eb62a8a8ae | UNDERPOWERED |
| sspec_520f127a1734d90457cd4442 | trade_date_block_shuffle | 9640 | BLOCKED | False | True | surrun_2dcbe94e529a60bac7499353 | UNDERPOWERED |
| sspec_520f127a1734d90457cd4442 | trade_date_block_shuffle | 9641 | BLOCKED | False | True | surrun_1c65939c4b52c578619cb71c | UNDERPOWERED |
| sspec_9793f7bfa9851ece64032bf8 | trade_date_block_shuffle | 9642 | BLOCKED | False | True | surrun_501e99a8ae7dda2dd45b338f | UNDERPOWERED |
| sspec_9793f7bfa9851ece64032bf8 | trade_date_block_shuffle | 9643 | BLOCKED | False | True | surrun_9d19532af67ed3c0dc05661b | UNDERPOWERED |
| sspec_9793f7bfa9851ece64032bf8 | trade_date_block_shuffle | 9644 | BLOCKED | False | True | surrun_f2db4932724afdc431f5d9da | UNDERPOWERED |
| sspec_41a7dcd4f4e4cffffdaf8053 | trade_date_block_shuffle | 9645 | BLOCKED | False | True | surrun_7e3d41bb4119c910ca9284da | UNDERPOWERED |
| sspec_41a7dcd4f4e4cffffdaf8053 | trade_date_block_shuffle | 9646 | BLOCKED | False | True | surrun_da8465ccd94b6ad37f80aed0 | UNDERPOWERED |
| sspec_41a7dcd4f4e4cffffdaf8053 | trade_date_block_shuffle | 9647 | BLOCKED | False | True | surrun_d67099354b6357b421faae9f | UNDERPOWERED |
| sspec_6befecec7cfb7f2c5b3fd8c7 | trade_date_block_shuffle | 9648 | BLOCKED | False | True | surrun_60fcd61ca9aabc000d8439cf | UNDERPOWERED |
| sspec_6befecec7cfb7f2c5b3fd8c7 | trade_date_block_shuffle | 9649 | BLOCKED | False | True | surrun_96b7dc6f2146cc24ca1ae596 | UNDERPOWERED |
| sspec_6befecec7cfb7f2c5b3fd8c7 | trade_date_block_shuffle | 9650 | BLOCKED | False | True | surrun_02c523c7603eeb477dcb949b | UNDERPOWERED |
| sspec_867c79cf4e938d9257746fb0 | trade_date_block_shuffle | 9651 | BLOCKED | False | True | surrun_edd1d873493a9e9120ed6b2a | UNDERPOWERED |
| sspec_867c79cf4e938d9257746fb0 | trade_date_block_shuffle | 9652 | BLOCKED | False | True | surrun_7706f26d23bc178e156a7ff9 | UNDERPOWERED |
| sspec_867c79cf4e938d9257746fb0 | trade_date_block_shuffle | 9653 | BLOCKED | False | True | surrun_9a60f29f020edffdf1f294b8 | UNDERPOWERED |
| sspec_5594a8f3d12c767aefcf73ce | trade_date_block_shuffle | 9654 | BLOCKED | False | True | surrun_c7e57488e7cec1e73c24123c | UNDERPOWERED |
| sspec_5594a8f3d12c767aefcf73ce | trade_date_block_shuffle | 9655 | BLOCKED | False | True | surrun_483066fbc4b64ec2cf9612c2 | UNDERPOWERED |
| sspec_5594a8f3d12c767aefcf73ce | trade_date_block_shuffle | 9656 | BLOCKED | False | True | surrun_0c9715b022f94d0898dd3523 | UNDERPOWERED |
| sspec_e1ac3cb2e0c7e222be6e0f58 | trade_date_block_shuffle | 9657 | BLOCKED | False | True | surrun_55381cf9270cd7148e16440a | UNDERPOWERED |
| sspec_e1ac3cb2e0c7e222be6e0f58 | trade_date_block_shuffle | 9658 | BLOCKED | False | True | surrun_6b6171bc0ff5a8fb38282414 | UNDERPOWERED |
| sspec_e1ac3cb2e0c7e222be6e0f58 | trade_date_block_shuffle | 9659 | BLOCKED | False | True | surrun_4517824b679d1649456ed733 | UNDERPOWERED |
| sspec_c2cca46451da082747ccf894 | trade_date_block_shuffle | 9660 | BLOCKED | False | True | surrun_ae56641409f0c03ad2fb90c7 | UNDERPOWERED |
| sspec_c2cca46451da082747ccf894 | trade_date_block_shuffle | 9661 | BLOCKED | False | True | surrun_4aa7535d1d1972a66da94cbd | UNDERPOWERED |
| sspec_c2cca46451da082747ccf894 | trade_date_block_shuffle | 9662 | BLOCKED | False | True | surrun_7f45a597e58979cc1936d558 | UNDERPOWERED |
| sspec_c025e8db6d95f0475f7defb1 | trade_date_block_shuffle | 9663 | BLOCKED | False | True | surrun_1223d128041e482e84c445d8 | UNDERPOWERED |
| sspec_c025e8db6d95f0475f7defb1 | trade_date_block_shuffle | 9664 | BLOCKED | False | True | surrun_547b6da2f7241e8a1ef6a8fc | UNDERPOWERED |
| sspec_c025e8db6d95f0475f7defb1 | trade_date_block_shuffle | 9665 | BLOCKED | False | True | surrun_36f75d936bb2e7fc986498bd | UNDERPOWERED |
| sspec_d80fc74961ac9aca6bad11e7 | trade_date_block_shuffle | 9666 | BLOCKED | False | True | surrun_39fc2f07dba089ece415bd3a | UNDERPOWERED |
| sspec_d80fc74961ac9aca6bad11e7 | trade_date_block_shuffle | 9667 | BLOCKED | False | True | surrun_baabe761c014a8e6e6af3b9d | UNDERPOWERED |
| sspec_d80fc74961ac9aca6bad11e7 | trade_date_block_shuffle | 9668 | BLOCKED | False | True | surrun_4ebd12436a47448158ded863 | UNDERPOWERED |
| sspec_91a919b77f6f8220213f68cf | trade_date_block_shuffle | 9669 | BLOCKED | False | True | surrun_3d0c779827f55c8b4cffb512 | UNDERPOWERED |
| sspec_91a919b77f6f8220213f68cf | trade_date_block_shuffle | 9670 | BLOCKED | False | True | surrun_eca9f032b2c5ba6fc3b3e6c1 | UNDERPOWERED |
| sspec_91a919b77f6f8220213f68cf | trade_date_block_shuffle | 9671 | BLOCKED | False | True | surrun_cfe7154744ada335526b5273 | UNDERPOWERED |
| sspec_70756efa7cc952ce60d7854e | trade_date_block_shuffle | 9672 | BLOCKED | False | True | surrun_393c2fe03aa229187bac170b | UNDERPOWERED |
| sspec_70756efa7cc952ce60d7854e | trade_date_block_shuffle | 9673 | BLOCKED | False | True | surrun_01b5edbb25a1c00205c8b78c | UNDERPOWERED |
| sspec_70756efa7cc952ce60d7854e | trade_date_block_shuffle | 9674 | BLOCKED | False | True | surrun_c284cf2272124e149118ef45 | UNDERPOWERED |
| sspec_c4ceba27c93f33eedce86f50 | trade_date_block_shuffle | 9675 | BLOCKED | False | True | surrun_84862a624bcd0a8f5a71cac8 | UNDERPOWERED |
| sspec_c4ceba27c93f33eedce86f50 | trade_date_block_shuffle | 9676 | BLOCKED | False | True | surrun_916e78414cf255bf156b8feb | UNDERPOWERED |
| sspec_c4ceba27c93f33eedce86f50 | trade_date_block_shuffle | 9677 | BLOCKED | False | True | surrun_ecd265dae7a882845bb4352a | UNDERPOWERED |
| sspec_f314f2efd00d36d1889d00fe | trade_date_block_shuffle | 9678 | BLOCKED | False | True | surrun_80aaa461b62a57b66bc09723 | UNDERPOWERED |
| sspec_f314f2efd00d36d1889d00fe | trade_date_block_shuffle | 9679 | BLOCKED | False | True | surrun_8ef7b4234701f97be509c6e7 | UNDERPOWERED |
| sspec_f314f2efd00d36d1889d00fe | trade_date_block_shuffle | 9680 | BLOCKED | False | True | surrun_d5a91b70ff27f2f813ff72b4 | UNDERPOWERED |
| sspec_fba1a8693a8229188942c231 | trade_date_block_shuffle | 9681 | BLOCKED | False | True | surrun_57405beaf31fd43901793d6f | UNDERPOWERED |
| sspec_fba1a8693a8229188942c231 | trade_date_block_shuffle | 9682 | BLOCKED | False | True | surrun_d437ad41118042bc48a465d6 | UNDERPOWERED |
| sspec_fba1a8693a8229188942c231 | trade_date_block_shuffle | 9683 | BLOCKED | False | True | surrun_65516f48b0d0db8e4e57f8f7 | UNDERPOWERED |
| sspec_a7e9731d3ef8c37d5a880801 | trade_date_block_shuffle | 9684 | BLOCKED | False | True | surrun_db9c82e6784a7f01260ef8ad | UNDERPOWERED |
| sspec_a7e9731d3ef8c37d5a880801 | trade_date_block_shuffle | 9685 | BLOCKED | False | True | surrun_c3cd49214005581c43441e0d | UNDERPOWERED |
| sspec_a7e9731d3ef8c37d5a880801 | trade_date_block_shuffle | 9686 | BLOCKED | False | True | surrun_76f6ee5fa34acfc1cafd3772 | UNDERPOWERED |
| sspec_3fd49fca02465bd9a11a2f23 | trade_date_block_shuffle | 9687 | BLOCKED | False | True | surrun_c7ab09dd5e5d5b4d3dd4e9f0 | UNDERPOWERED |
| sspec_3fd49fca02465bd9a11a2f23 | trade_date_block_shuffle | 9688 | BLOCKED | False | True | surrun_1402c60c11b0245215b42f33 | UNDERPOWERED |
| sspec_3fd49fca02465bd9a11a2f23 | trade_date_block_shuffle | 9689 | BLOCKED | False | True | surrun_fc9cdf2bcc76de7a85d5ca02 | UNDERPOWERED |
| sspec_5cc9cbcb196e6baa32920952 | trade_date_block_shuffle | 9690 | BLOCKED | False | True | surrun_4aa7bcd2e5edd989f86a1a68 | UNDERPOWERED |
| sspec_5cc9cbcb196e6baa32920952 | trade_date_block_shuffle | 9691 | BLOCKED | False | True | surrun_a64bfd7c3c8e0b341379bdb9 | UNDERPOWERED |
| sspec_5cc9cbcb196e6baa32920952 | trade_date_block_shuffle | 9692 | BLOCKED | False | True | surrun_b34bf977c39f87f86e38d2bd | UNDERPOWERED |
| sspec_8ada06420b84793baca8c62f | trade_date_block_shuffle | 9693 | BLOCKED | False | True | surrun_fa7ba43278dd167e774af95e | UNDERPOWERED |
| sspec_8ada06420b84793baca8c62f | trade_date_block_shuffle | 9694 | BLOCKED | False | True | surrun_23dce3f362816f9c7f958a0c | UNDERPOWERED |
| sspec_8ada06420b84793baca8c62f | trade_date_block_shuffle | 9695 | BLOCKED | False | True | surrun_9b0ddd8b20d16ef22d200b5e | UNDERPOWERED |
| sspec_9987f684a025b26d844db5ed | trade_date_block_shuffle | 9696 | BLOCKED | False | True | surrun_06fa811530225e4d26c71669 | UNDERPOWERED |
| sspec_9987f684a025b26d844db5ed | trade_date_block_shuffle | 9697 | BLOCKED | False | True | surrun_5767789df4bf0b1d99c8a689 | UNDERPOWERED |
| sspec_9987f684a025b26d844db5ed | trade_date_block_shuffle | 9698 | BLOCKED | False | True | surrun_9084540630199386f8e4aa00 | UNDERPOWERED |
| sspec_84f839dfa7372cdeffac6257 | trade_date_block_shuffle | 9699 | BLOCKED | False | True | surrun_07556cf81d34ca7a1b8920cd | UNDERPOWERED |
| sspec_84f839dfa7372cdeffac6257 | trade_date_block_shuffle | 9700 | BLOCKED | False | True | surrun_6e727d67d49ebd11e7105418 | UNDERPOWERED |
| sspec_84f839dfa7372cdeffac6257 | trade_date_block_shuffle | 9701 | BLOCKED | False | True | surrun_a0c0b9e05fe302ed405fe36c | UNDERPOWERED |
| sspec_0afcbe810bd46b05ae02b19c | trade_date_block_shuffle | 9702 | BLOCKED | False | True | surrun_59057af7266ed680e14308fe | UNDERPOWERED |
| sspec_0afcbe810bd46b05ae02b19c | trade_date_block_shuffle | 9703 | BLOCKED | False | True | surrun_84f0bad2a8e3ce2b2615f328 | UNDERPOWERED |
| sspec_0afcbe810bd46b05ae02b19c | trade_date_block_shuffle | 9704 | BLOCKED | False | True | surrun_e6bd2b5304ed8b2f6cff79ff | UNDERPOWERED |
| sspec_8d0db05ad7c58c4643fe077b | trade_date_block_shuffle | 9705 | BLOCKED | False | True | surrun_2d6ca8968a13a089ab1e0230 | UNDERPOWERED |
| sspec_8d0db05ad7c58c4643fe077b | trade_date_block_shuffle | 9706 | BLOCKED | False | True | surrun_0a82d6a150bb91db9f810178 | UNDERPOWERED |
| sspec_8d0db05ad7c58c4643fe077b | trade_date_block_shuffle | 9707 | BLOCKED | False | True | surrun_39488c912f17b75ec04f1aae | UNDERPOWERED |
| sspec_d7f40557b1d8042fbdc43bed | trade_date_block_shuffle | 9708 | BLOCKED | False | True | surrun_13e09ede468fa9c64a7c9f38 | UNDERPOWERED |
| sspec_d7f40557b1d8042fbdc43bed | trade_date_block_shuffle | 9709 | BLOCKED | False | True | surrun_50291f7f4166204e12c0d707 | UNDERPOWERED |
| sspec_d7f40557b1d8042fbdc43bed | trade_date_block_shuffle | 9710 | BLOCKED | False | True | surrun_afee01f68657078c7206293b | UNDERPOWERED |
| sspec_05acd70e6de784ddf227f5eb | trade_date_block_shuffle | 9711 | BLOCKED | False | True | surrun_20d33a375a975649dd684b68 | UNDERPOWERED |
| sspec_05acd70e6de784ddf227f5eb | trade_date_block_shuffle | 9712 | BLOCKED | False | True | surrun_23fb2b7c06fb46b65ca2c74a | UNDERPOWERED |
| sspec_05acd70e6de784ddf227f5eb | trade_date_block_shuffle | 9713 | BLOCKED | False | True | surrun_ee085505615a61fd1489b8ad | UNDERPOWERED |
| sspec_87e724c7e9377b33803ae628 | trade_date_block_shuffle | 9714 | BLOCKED | False | True | surrun_d5d57b2e66d6ba53e3c3de0f | UNDERPOWERED |
| sspec_87e724c7e9377b33803ae628 | trade_date_block_shuffle | 9715 | BLOCKED | False | True | surrun_d0ad2d4a4e990ce5b5ab9f11 | UNDERPOWERED |
| sspec_87e724c7e9377b33803ae628 | trade_date_block_shuffle | 9716 | BLOCKED | False | True | surrun_b12061677e49eb8217a62043 | UNDERPOWERED |
| sspec_f9faa8f59f3131a1e51a7550 | trade_date_block_shuffle | 9717 | BLOCKED | False | True | surrun_3030a9eaae03fecf7275fe79 | UNDERPOWERED |
| sspec_f9faa8f59f3131a1e51a7550 | trade_date_block_shuffle | 9718 | BLOCKED | False | True | surrun_64a2d6c1278554095e18c8da | UNDERPOWERED |
| sspec_f9faa8f59f3131a1e51a7550 | trade_date_block_shuffle | 9719 | BLOCKED | False | True | surrun_1c728ef8b0dbb335acde82ed | UNDERPOWERED |
| sspec_5a135cae15ed881f04ae6fa5 | trade_date_block_shuffle | 9720 | BLOCKED | False | True | surrun_9e0515853d30c13b983848fe | UNDERPOWERED |
| sspec_5a135cae15ed881f04ae6fa5 | trade_date_block_shuffle | 9721 | BLOCKED | False | True | surrun_6779a770837f6c3f9719396b | UNDERPOWERED |
| sspec_5a135cae15ed881f04ae6fa5 | trade_date_block_shuffle | 9722 | BLOCKED | False | True | surrun_d56bf620813eac713b9a3076 | UNDERPOWERED |
| sspec_72d581628d90f8918dac1e47 | trade_date_block_shuffle | 9723 | BLOCKED | False | True | surrun_9167137adcad673789dce119 | UNDERPOWERED |
| sspec_72d581628d90f8918dac1e47 | trade_date_block_shuffle | 9724 | BLOCKED | False | True | surrun_e60c0e3f278c4ef7d2a7c8ae | UNDERPOWERED |
| sspec_72d581628d90f8918dac1e47 | trade_date_block_shuffle | 9725 | BLOCKED | False | True | surrun_aa68ed6522cc7c11c7cb35fe | UNDERPOWERED |
| sspec_8022f2c052c5a2dd40bd56bd | trade_date_block_shuffle | 9726 | BLOCKED | False | True | surrun_9db8ae66ced0117a82c75523 | UNDERPOWERED |
| sspec_8022f2c052c5a2dd40bd56bd | trade_date_block_shuffle | 9727 | BLOCKED | False | True | surrun_cd022399c267570bd93d2f78 | UNDERPOWERED |
| sspec_8022f2c052c5a2dd40bd56bd | trade_date_block_shuffle | 9728 | BLOCKED | False | True | surrun_0a6b243ef80e33aedc340997 | UNDERPOWERED |
| sspec_c64d85180ea048aa542b734a | trade_date_block_shuffle | 9729 | BLOCKED | False | True | surrun_0230114c8d6caf7eb4444c0e | UNDERPOWERED |
| sspec_c64d85180ea048aa542b734a | trade_date_block_shuffle | 9730 | BLOCKED | False | True | surrun_861fa306916fdace8e0ecd5a | UNDERPOWERED |
| sspec_c64d85180ea048aa542b734a | trade_date_block_shuffle | 9731 | BLOCKED | False | True | surrun_aef370e737988a1631dc74f3 | UNDERPOWERED |
| sspec_3655e6865a834c8dead47c06 | trade_date_block_shuffle | 9732 | BLOCKED | False | True | surrun_669bc04adab1457d706d1079 | UNDERPOWERED |
| sspec_3655e6865a834c8dead47c06 | trade_date_block_shuffle | 9733 | BLOCKED | False | True | surrun_624723cccb1ef1c4ca89ba5d | UNDERPOWERED |
| sspec_3655e6865a834c8dead47c06 | trade_date_block_shuffle | 9734 | BLOCKED | False | True | surrun_80916a8cb24c22d09f1f1122 | UNDERPOWERED |
| sspec_ef5252b2cab7faab1a15ad15 | trade_date_block_shuffle | 9735 | BLOCKED | False | True | surrun_83d4b62e26c208c6eed6e0c8 | UNDERPOWERED |
| sspec_ef5252b2cab7faab1a15ad15 | trade_date_block_shuffle | 9736 | BLOCKED | False | True | surrun_65b1e3d597bc437e382b7621 | UNDERPOWERED |
| sspec_ef5252b2cab7faab1a15ad15 | trade_date_block_shuffle | 9737 | BLOCKED | False | True | surrun_5d1eb9f34d74700f52aa87bd | UNDERPOWERED |
| sspec_83bc285f4ff066119a9600cb | trade_date_block_shuffle | 9738 | BLOCKED | False | True | surrun_3c891166088eeafd64710ba3 | UNDERPOWERED |
| sspec_83bc285f4ff066119a9600cb | trade_date_block_shuffle | 9739 | BLOCKED | False | True | surrun_9e88557edd0185880914887b | UNDERPOWERED |
| sspec_83bc285f4ff066119a9600cb | trade_date_block_shuffle | 9740 | BLOCKED | False | True | surrun_0da9151a6151b02cd3733cf5 | UNDERPOWERED |
| sspec_391c5ea571770ece430c303a | trade_date_block_shuffle | 9741 | BLOCKED | False | True | surrun_3d43e3153f5cd4c82519b1f3 | UNDERPOWERED |
| sspec_391c5ea571770ece430c303a | trade_date_block_shuffle | 9742 | BLOCKED | False | True | surrun_1649c0b5c7b20c8953147dac | UNDERPOWERED |
| sspec_391c5ea571770ece430c303a | trade_date_block_shuffle | 9743 | BLOCKED | False | True | surrun_0d0a9f51edbca976323deedb | UNDERPOWERED |
| sspec_35729e0c9b8ada663b8becb8 | trade_date_block_shuffle | 9744 | BLOCKED | False | True | surrun_ddc32b3600d5ebe2b0befe1a | UNDERPOWERED |
| sspec_35729e0c9b8ada663b8becb8 | trade_date_block_shuffle | 9745 | BLOCKED | False | True | surrun_83df1c559af768b5d5bdd4d2 | UNDERPOWERED |
| sspec_35729e0c9b8ada663b8becb8 | trade_date_block_shuffle | 9746 | BLOCKED | False | True | surrun_06524577d8e7f393bb10c8a0 | UNDERPOWERED |
| sspec_4d6094e489ece633dfdffd1c | trade_date_block_shuffle | 9747 | BLOCKED | False | True | surrun_167f9ad70098918ea2179115 | UNDERPOWERED |
| sspec_4d6094e489ece633dfdffd1c | trade_date_block_shuffle | 9748 | BLOCKED | False | True | surrun_5c47b0dd1c691fbf1515498a | UNDERPOWERED |
| sspec_4d6094e489ece633dfdffd1c | trade_date_block_shuffle | 9749 | BLOCKED | False | True | surrun_de8bfaa66197686e5afe565d | UNDERPOWERED |
| sspec_fef006f9cc9e1213b8236939 | trade_date_block_shuffle | 9750 | BLOCKED | False | True | surrun_f723def6950843e9b815b418 | UNDERPOWERED |
| sspec_fef006f9cc9e1213b8236939 | trade_date_block_shuffle | 9751 | BLOCKED | False | True | surrun_335125064543aecdf50c163b | UNDERPOWERED |
| sspec_fef006f9cc9e1213b8236939 | trade_date_block_shuffle | 9752 | BLOCKED | False | True | surrun_15ea94a6a1a06ddc9d2c0222 | UNDERPOWERED |
| sspec_d5ff5892990f8e4e9677b86a | trade_date_block_shuffle | 9753 | BLOCKED | False | True | surrun_1678185ac855c7586a4239be | UNDERPOWERED |
| sspec_d5ff5892990f8e4e9677b86a | trade_date_block_shuffle | 9754 | BLOCKED | False | True | surrun_e0d2952a17f7b3dfb117f3ee | UNDERPOWERED |
| sspec_d5ff5892990f8e4e9677b86a | trade_date_block_shuffle | 9755 | BLOCKED | False | True | surrun_64ec43c5d28dfbaa6d480c16 | UNDERPOWERED |
| sspec_6cab22ffd94a58f5eee335b7 | trade_date_block_shuffle | 9756 | BLOCKED | False | True | surrun_937e7c2ecedea9f62da5c8f0 | UNDERPOWERED |
| sspec_6cab22ffd94a58f5eee335b7 | trade_date_block_shuffle | 9757 | BLOCKED | False | True | surrun_394006c292479a3a8a9afbf2 | UNDERPOWERED |
| sspec_6cab22ffd94a58f5eee335b7 | trade_date_block_shuffle | 9758 | BLOCKED | False | True | surrun_8ff85013c405e6ab5900d376 | UNDERPOWERED |
| sspec_db017ceb7b249fd02c3109e4 | trade_date_block_shuffle | 9759 | BLOCKED | False | True | surrun_f3efefd55186b781d87338a7 | UNDERPOWERED |
| sspec_db017ceb7b249fd02c3109e4 | trade_date_block_shuffle | 9760 | BLOCKED | False | True | surrun_8960afed36e8048fbec7dddb | UNDERPOWERED |
| sspec_db017ceb7b249fd02c3109e4 | trade_date_block_shuffle | 9761 | BLOCKED | False | True | surrun_eb722c89252f8d2badbcfb4d | UNDERPOWERED |
| sspec_167bac07abdbb940c692d3f4 | trade_date_block_shuffle | 9762 | BLOCKED | False | True | surrun_301b031e4bc73f8d469454f9 | UNDERPOWERED |
| sspec_167bac07abdbb940c692d3f4 | trade_date_block_shuffle | 9763 | BLOCKED | False | True | surrun_731450ff532c9a35f1320441 | UNDERPOWERED |
| sspec_167bac07abdbb940c692d3f4 | trade_date_block_shuffle | 9764 | BLOCKED | False | True | surrun_ff123adc78c56a03440b44c0 | UNDERPOWERED |
| sspec_c7564368c843e9180f3b9c5d | trade_date_block_shuffle | 9765 | BLOCKED | False | True | surrun_ffb38e4e51ee7459a991d1c3 | UNDERPOWERED |
| sspec_c7564368c843e9180f3b9c5d | trade_date_block_shuffle | 9766 | BLOCKED | False | True | surrun_1a362da954cbbb6d87a94268 | UNDERPOWERED |
| sspec_c7564368c843e9180f3b9c5d | trade_date_block_shuffle | 9767 | BLOCKED | False | True | surrun_6eafa3d6db5c3680407cfd28 | UNDERPOWERED |
| sspec_64e18de1ab7562b175c5abdf | trade_date_block_shuffle | 9768 | BLOCKED | False | True | surrun_fa0ea2aff013af0e923e04de | UNDERPOWERED |
| sspec_64e18de1ab7562b175c5abdf | trade_date_block_shuffle | 9769 | BLOCKED | False | True | surrun_49dd7211cca1a773a3ec9cda | UNDERPOWERED |
| sspec_64e18de1ab7562b175c5abdf | trade_date_block_shuffle | 9770 | BLOCKED | False | True | surrun_3a09c5eff4f596f708dc1862 | UNDERPOWERED |
| sspec_2a25fc4b4ea0e424771ccc96 | trade_date_block_shuffle | 9771 | BLOCKED | False | True | surrun_40a4e6d918682065dd23c7b9 | UNDERPOWERED |
| sspec_2a25fc4b4ea0e424771ccc96 | trade_date_block_shuffle | 9772 | BLOCKED | False | True | surrun_b6b0cc2aaca6b9f9c88f9190 | UNDERPOWERED |
| sspec_2a25fc4b4ea0e424771ccc96 | trade_date_block_shuffle | 9773 | BLOCKED | False | True | surrun_6683248a668171e7304411d9 | UNDERPOWERED |
| sspec_665b44b6bb64c6c524834096 | trade_date_block_shuffle | 9774 | BLOCKED | False | True | surrun_028c2990545f180fd2e678a0 | UNDERPOWERED |
| sspec_665b44b6bb64c6c524834096 | trade_date_block_shuffle | 9775 | BLOCKED | False | True | surrun_ae07b6952b7e0a2b2760c1e6 | UNDERPOWERED |
| sspec_665b44b6bb64c6c524834096 | trade_date_block_shuffle | 9776 | BLOCKED | False | True | surrun_8a0c311ff5866b79a9e6028b | UNDERPOWERED |
| sspec_c589d1eed7e4d6323b05b9c2 | trade_date_block_shuffle | 9777 | BLOCKED | False | True | surrun_164d186eeb484cba5164387e | UNDERPOWERED |
| sspec_c589d1eed7e4d6323b05b9c2 | trade_date_block_shuffle | 9778 | BLOCKED | False | True | surrun_a6ab50fbd130600c9267b1fe | UNDERPOWERED |
| sspec_c589d1eed7e4d6323b05b9c2 | trade_date_block_shuffle | 9779 | BLOCKED | False | True | surrun_73272f9470b078c18af57bbe | UNDERPOWERED |
| sspec_b71b3b2357dbb70f673c18fc | trade_date_block_shuffle | 9780 | BLOCKED | False | True | surrun_a91d6bbee04a9fd45760c7b2 | UNDERPOWERED |
| sspec_b71b3b2357dbb70f673c18fc | trade_date_block_shuffle | 9781 | BLOCKED | False | True | surrun_42b8149928ef2adcab2604ce | UNDERPOWERED |
| sspec_b71b3b2357dbb70f673c18fc | trade_date_block_shuffle | 9782 | BLOCKED | False | True | surrun_9d0117e24e7841d5ba0d12cf | UNDERPOWERED |
| sspec_601a6336820a94d988b97648 | trade_date_block_shuffle | 9783 | BLOCKED | False | True | surrun_bb084da5d54ad12fbd5fa5a8 | UNDERPOWERED |
| sspec_601a6336820a94d988b97648 | trade_date_block_shuffle | 9784 | BLOCKED | False | True | surrun_e2d5e363d48ee8054995cd7f | UNDERPOWERED |
| sspec_601a6336820a94d988b97648 | trade_date_block_shuffle | 9785 | BLOCKED | False | True | surrun_775bed2a8e2ecf5a41d33db8 | UNDERPOWERED |
| sspec_b2481e16b39e5bb5c36e9077 | trade_date_block_shuffle | 9786 | BLOCKED | False | True | surrun_fce3be490576e651b3f3b793 | UNDERPOWERED |
| sspec_b2481e16b39e5bb5c36e9077 | trade_date_block_shuffle | 9787 | BLOCKED | False | True | surrun_fffc927e944c01b637963746 | UNDERPOWERED |
| sspec_b2481e16b39e5bb5c36e9077 | trade_date_block_shuffle | 9788 | BLOCKED | False | True | surrun_4002f4f5a9f867543cb880b7 | UNDERPOWERED |
| sspec_da7f34f66bcae76f5de31456 | trade_date_block_shuffle | 9789 | BLOCKED | False | True | surrun_6fa692c81e7ccf6d0925e296 | UNDERPOWERED |
| sspec_da7f34f66bcae76f5de31456 | trade_date_block_shuffle | 9790 | BLOCKED | False | True | surrun_6bdd2bc2f5d0b105dd5ff973 | UNDERPOWERED |
| sspec_da7f34f66bcae76f5de31456 | trade_date_block_shuffle | 9791 | BLOCKED | False | True | surrun_de03984e11a92ea414707f25 | UNDERPOWERED |
| sspec_08b927cfed36292db6022e76 | trade_date_block_shuffle | 9792 | BLOCKED | False | True | surrun_19d83a33edd899204a971174 | UNDERPOWERED |
| sspec_08b927cfed36292db6022e76 | trade_date_block_shuffle | 9793 | BLOCKED | False | True | surrun_c49f08f3ad3bea4dbcbf5364 | UNDERPOWERED |
| sspec_08b927cfed36292db6022e76 | trade_date_block_shuffle | 9794 | BLOCKED | False | True | surrun_64afa9ee1a9f88763401b8c8 | UNDERPOWERED |
| sspec_9deffcfe1cd9f8eed3345f3b | trade_date_block_shuffle | 9795 | BLOCKED | False | True | surrun_4babe62709e621d06e70db6c | UNDERPOWERED |
| sspec_9deffcfe1cd9f8eed3345f3b | trade_date_block_shuffle | 9796 | BLOCKED | False | True | surrun_d7ac442eec2e570df8dae696 | UNDERPOWERED |
| sspec_9deffcfe1cd9f8eed3345f3b | trade_date_block_shuffle | 9797 | BLOCKED | False | True | surrun_848fbac23c562b225834963b | UNDERPOWERED |
| sspec_068dee8a1c12196a48ff6e38 | trade_date_block_shuffle | 9798 | BLOCKED | False | True | surrun_10e89b26e09b8776cdc06a9e | UNDERPOWERED |
| sspec_068dee8a1c12196a48ff6e38 | trade_date_block_shuffle | 9799 | BLOCKED | False | True | surrun_95a08d9a335ea4eecef12742 | UNDERPOWERED |
| sspec_068dee8a1c12196a48ff6e38 | trade_date_block_shuffle | 9800 | BLOCKED | False | True | surrun_cae2b9ce09132399c59b11cf | UNDERPOWERED |
| sspec_22b9a510d85ae10e9a235231 | trade_date_block_shuffle | 9801 | BLOCKED | False | True | surrun_f8bb049db7fc225c729b8491 | UNDERPOWERED |
| sspec_22b9a510d85ae10e9a235231 | trade_date_block_shuffle | 9802 | BLOCKED | False | True | surrun_a90268f2e3db3c2f2e3f35b4 | UNDERPOWERED |
| sspec_22b9a510d85ae10e9a235231 | trade_date_block_shuffle | 9803 | BLOCKED | False | True | surrun_f9b38e6acb27f5705bb8f7ec | UNDERPOWERED |
| sspec_d05c98f1b32052870140910f | trade_date_block_shuffle | 9804 | BLOCKED | False | True | surrun_243f289fd0854ee202214ff1 | UNDERPOWERED |
| sspec_d05c98f1b32052870140910f | trade_date_block_shuffle | 9805 | BLOCKED | False | True | surrun_088475994eddb83b7a3f2392 | UNDERPOWERED |
| sspec_d05c98f1b32052870140910f | trade_date_block_shuffle | 9806 | BLOCKED | False | True | surrun_ca5b9db4dc718bf641e0739a | UNDERPOWERED |
| sspec_bb21a754d9c207aab9833762 | trade_date_block_shuffle | 9807 | BLOCKED | False | True | surrun_bbbc70f5467194391c347411 | UNDERPOWERED |
| sspec_bb21a754d9c207aab9833762 | trade_date_block_shuffle | 9808 | BLOCKED | False | True | surrun_ed3e6105d6d094d954f0dffc | UNDERPOWERED |
| sspec_bb21a754d9c207aab9833762 | trade_date_block_shuffle | 9809 | BLOCKED | False | True | surrun_faf61ef6b5d73248d85aaecc | UNDERPOWERED |
| sspec_5f831db8c0e9f95a81f6858f | trade_date_block_shuffle | 9810 | BLOCKED | False | True | surrun_c0f491f8eb16863ccd9b6cf6 | UNDERPOWERED |
| sspec_5f831db8c0e9f95a81f6858f | trade_date_block_shuffle | 9811 | BLOCKED | False | True | surrun_78459ee4cd49468103b009c0 | UNDERPOWERED |
| sspec_5f831db8c0e9f95a81f6858f | trade_date_block_shuffle | 9812 | BLOCKED | False | True | surrun_1c060800a809519ee0c83685 | UNDERPOWERED |
| sspec_7c721ada57890200ad5316fc | trade_date_block_shuffle | 9813 | BLOCKED | False | True | surrun_830893db7f848d1d6999985d | UNDERPOWERED |
| sspec_7c721ada57890200ad5316fc | trade_date_block_shuffle | 9814 | BLOCKED | False | True | surrun_d5ffdb3d8dfffd50e5f070f2 | UNDERPOWERED |
| sspec_7c721ada57890200ad5316fc | trade_date_block_shuffle | 9815 | BLOCKED | False | True | surrun_49053a857c9af9d13bac0439 | UNDERPOWERED |
| sspec_29fc1e53a2fa05d7a46d9100 | trade_date_block_shuffle | 9816 | BLOCKED | False | True | surrun_9af9896493091bc4161160bd | UNDERPOWERED |
| sspec_29fc1e53a2fa05d7a46d9100 | trade_date_block_shuffle | 9817 | BLOCKED | False | True | surrun_a1241284d75a476b3acdb8ff | UNDERPOWERED |
| sspec_29fc1e53a2fa05d7a46d9100 | trade_date_block_shuffle | 9818 | BLOCKED | False | True | surrun_47d1a4b23b08ea2198f8d163 | UNDERPOWERED |
| sspec_148f1fd71000c07947d55d1a | trade_date_block_shuffle | 9819 | BLOCKED | False | True | surrun_44d9e33a2e51bb684bf1591e | UNDERPOWERED |
| sspec_148f1fd71000c07947d55d1a | trade_date_block_shuffle | 9820 | BLOCKED | False | True | surrun_760f5e7e9535f9a6275087b8 | UNDERPOWERED |
| sspec_148f1fd71000c07947d55d1a | trade_date_block_shuffle | 9821 | BLOCKED | False | True | surrun_e94a5db2e5ec7cdc4a35ad1d | UNDERPOWERED |
| sspec_70c576a78832f1ef384c3d76 | trade_date_block_shuffle | 9822 | BLOCKED | False | True | surrun_41d68f2c1d7b1b86eb64cb8f | UNDERPOWERED |
| sspec_70c576a78832f1ef384c3d76 | trade_date_block_shuffle | 9823 | BLOCKED | False | True | surrun_7ab2f1f61a7af34fa6926b52 | UNDERPOWERED |
| sspec_70c576a78832f1ef384c3d76 | trade_date_block_shuffle | 9824 | BLOCKED | False | True | surrun_b48b8b07c68fa6bb7514e6dc | UNDERPOWERED |
| sspec_3d559156c808892bb51553dc | trade_date_block_shuffle | 9825 | BLOCKED | False | True | surrun_36085feca901f8c8d2549cc5 | UNDERPOWERED |
| sspec_3d559156c808892bb51553dc | trade_date_block_shuffle | 9826 | BLOCKED | False | True | surrun_af37ab889cf4a27987012a92 | UNDERPOWERED |
| sspec_3d559156c808892bb51553dc | trade_date_block_shuffle | 9827 | BLOCKED | False | True | surrun_8ac15e0c631f90df39986123 | UNDERPOWERED |
| sspec_4b3219b22b82969e17986b28 | trade_date_block_shuffle | 9828 | BLOCKED | False | True | surrun_844566ecf2f308c428989529 | UNDERPOWERED |
| sspec_4b3219b22b82969e17986b28 | trade_date_block_shuffle | 9829 | BLOCKED | False | True | surrun_ecc69b3b64fa2bade1175d01 | UNDERPOWERED |
| sspec_4b3219b22b82969e17986b28 | trade_date_block_shuffle | 9830 | BLOCKED | False | True | surrun_4c3a5ab05f3fead6b3cf3518 | UNDERPOWERED |
| sspec_831f46078607ce17ef1045ec | trade_date_block_shuffle | 9831 | BLOCKED | False | True | surrun_14a848338b89ed642015ca73 | UNDERPOWERED |
| sspec_831f46078607ce17ef1045ec | trade_date_block_shuffle | 9832 | BLOCKED | False | True | surrun_c07a6000a3564b3784789e34 | UNDERPOWERED |
| sspec_831f46078607ce17ef1045ec | trade_date_block_shuffle | 9833 | BLOCKED | False | True | surrun_5524cd88680e503bd42c20f2 | UNDERPOWERED |
| sspec_347c0f1c475b1f8e5ea8db95 | trade_date_block_shuffle | 9834 | BLOCKED | False | True | surrun_4608fdb2beb765f0261295ce | UNDERPOWERED |
| sspec_347c0f1c475b1f8e5ea8db95 | trade_date_block_shuffle | 9835 | BLOCKED | False | True | surrun_f4df79c67bb691546ab2851b | UNDERPOWERED |
| sspec_347c0f1c475b1f8e5ea8db95 | trade_date_block_shuffle | 9836 | BLOCKED | False | True | surrun_4d31cf2c099b1ab0d86b0103 | UNDERPOWERED |
| sspec_7832d85519da01ba5e61c9ad | trade_date_block_shuffle | 9837 | BLOCKED | False | True | surrun_070292344b7ebf9b7459a0e0 | UNDERPOWERED |
| sspec_7832d85519da01ba5e61c9ad | trade_date_block_shuffle | 9838 | BLOCKED | False | True | surrun_b414ec1c8deea9b4ec1baca3 | UNDERPOWERED |
| sspec_7832d85519da01ba5e61c9ad | trade_date_block_shuffle | 9839 | BLOCKED | False | True | surrun_6ffa4913e363b9b59a43c520 | UNDERPOWERED |
| sspec_1828472fa677307f3d940d11 | trade_date_block_shuffle | 9840 | BLOCKED | False | True | surrun_7b2ad9388d7025816324652c | UNDERPOWERED |
| sspec_1828472fa677307f3d940d11 | trade_date_block_shuffle | 9841 | BLOCKED | False | True | surrun_ece4795cb438149770ca9b91 | UNDERPOWERED |
| sspec_1828472fa677307f3d940d11 | trade_date_block_shuffle | 9842 | BLOCKED | False | True | surrun_8992f1db4a243731db343941 | UNDERPOWERED |
| sspec_0fccfd79c440ecddb69bb2dc | trade_date_block_shuffle | 9843 | BLOCKED | False | True | surrun_0f4ae02a023f5cd9ee82de62 | UNDERPOWERED |
| sspec_0fccfd79c440ecddb69bb2dc | trade_date_block_shuffle | 9844 | BLOCKED | False | True | surrun_b780ebf6bae15f276812473f | UNDERPOWERED |
| sspec_0fccfd79c440ecddb69bb2dc | trade_date_block_shuffle | 9845 | BLOCKED | False | True | surrun_b5c2252fa939b2d2e1bc3549 | UNDERPOWERED |
| sspec_fd61d11a0368a7fe72cc8ade | trade_date_block_shuffle | 9846 | BLOCKED | False | True | surrun_5a8c3acda2f3a02a0cda5bfe | UNDERPOWERED |
| sspec_fd61d11a0368a7fe72cc8ade | trade_date_block_shuffle | 9847 | BLOCKED | False | True | surrun_58c1bc45534f0f5512bb792b | UNDERPOWERED |
| sspec_fd61d11a0368a7fe72cc8ade | trade_date_block_shuffle | 9848 | BLOCKED | False | True | surrun_b0b7a53a31b9e82816e5b00d | UNDERPOWERED |
| sspec_dd125675e5b4d7469ee982fc | trade_date_block_shuffle | 9849 | BLOCKED | False | True | surrun_7a1980fe5a88635d5da6ff04 | UNDERPOWERED |
| sspec_dd125675e5b4d7469ee982fc | trade_date_block_shuffle | 9850 | BLOCKED | False | True | surrun_7f22124afe8c433dadc4fe6d | UNDERPOWERED |
| sspec_dd125675e5b4d7469ee982fc | trade_date_block_shuffle | 9851 | BLOCKED | False | True | surrun_e49e4f4d0e8850876e3357cd | UNDERPOWERED |
| sspec_9fbb26feebc7dc9e6eb4e31c | trade_date_block_shuffle | 9852 | BLOCKED | False | True | surrun_8897bc7cd5e01290ffe9ba46 | UNDERPOWERED |
| sspec_9fbb26feebc7dc9e6eb4e31c | trade_date_block_shuffle | 9853 | BLOCKED | False | True | surrun_b4b0abc3d77186b80b4acade | UNDERPOWERED |
| sspec_9fbb26feebc7dc9e6eb4e31c | trade_date_block_shuffle | 9854 | BLOCKED | False | True | surrun_33793ac9c542ff5fd138f9a5 | UNDERPOWERED |
| sspec_dce720a6b60901a7d213cd90 | trade_date_block_shuffle | 9855 | BLOCKED | False | True | surrun_e460c58386bc032c57a764d6 | UNDERPOWERED |
| sspec_dce720a6b60901a7d213cd90 | trade_date_block_shuffle | 9856 | BLOCKED | False | True | surrun_9e2c987886cb8d2760b4800d | UNDERPOWERED |
| sspec_dce720a6b60901a7d213cd90 | trade_date_block_shuffle | 9857 | BLOCKED | False | True | surrun_c1f944b47ec0940c9dcfff25 | UNDERPOWERED |
| sspec_7999f013e149e904dc230f2a | trade_date_block_shuffle | 9858 | BLOCKED | False | True | surrun_6f5ee42bbfffe48acf764ac4 | UNDERPOWERED |
| sspec_7999f013e149e904dc230f2a | trade_date_block_shuffle | 9859 | BLOCKED | False | True | surrun_35d7fd5f12ac240ce111061e | UNDERPOWERED |
| sspec_7999f013e149e904dc230f2a | trade_date_block_shuffle | 9860 | BLOCKED | False | True | surrun_8a7711d5ac3a0c806f8e722d | UNDERPOWERED |
| sspec_5b667204dc6b75ecc152f0d1 | trade_date_block_shuffle | 9861 | BLOCKED | False | True | surrun_c441f7cff7f5b1ef4d12272d | UNDERPOWERED |
| sspec_5b667204dc6b75ecc152f0d1 | trade_date_block_shuffle | 9862 | BLOCKED | False | True | surrun_236c2398ad2e7114922d79e8 | UNDERPOWERED |
| sspec_5b667204dc6b75ecc152f0d1 | trade_date_block_shuffle | 9863 | BLOCKED | False | True | surrun_1ac4963cfe4b28e65cdd5d93 | UNDERPOWERED |
| sspec_e603b3075bc6e35b8cbc3be3 | trade_date_block_shuffle | 9864 | BLOCKED | False | True | surrun_255a2b063ea7c7e8e4cdb8ed | UNDERPOWERED |
| sspec_e603b3075bc6e35b8cbc3be3 | trade_date_block_shuffle | 9865 | BLOCKED | False | True | surrun_963b56c04e858b754752a9ec | UNDERPOWERED |
| sspec_e603b3075bc6e35b8cbc3be3 | trade_date_block_shuffle | 9866 | BLOCKED | False | True | surrun_7acf51cb52bc5908aff818ed | UNDERPOWERED |
| sspec_eef5b1d10312d055b5cf41c8 | trade_date_block_shuffle | 9867 | BLOCKED | False | True | surrun_623dc8ca35c86e77b2cf7641 | UNDERPOWERED |
| sspec_eef5b1d10312d055b5cf41c8 | trade_date_block_shuffle | 9868 | BLOCKED | False | True | surrun_e9d52c0a29ee913569818d2e | UNDERPOWERED |
| sspec_eef5b1d10312d055b5cf41c8 | trade_date_block_shuffle | 9869 | BLOCKED | False | True | surrun_7c135bf8d7a08f4bd25e2f33 | UNDERPOWERED |
| sspec_222ab384a2e47bdefee9ba58 | trade_date_block_shuffle | 9870 | BLOCKED | False | True | surrun_b23129faf3756106fd834c8b | UNDERPOWERED |
| sspec_222ab384a2e47bdefee9ba58 | trade_date_block_shuffle | 9871 | BLOCKED | False | True | surrun_474e0292f03fb164081bdef6 | UNDERPOWERED |
| sspec_222ab384a2e47bdefee9ba58 | trade_date_block_shuffle | 9872 | BLOCKED | False | True | surrun_98678c15a0c097d0b5f2b703 | UNDERPOWERED |
| sspec_0b99fe38aef1aab26e375a42 | trade_date_block_shuffle | 9873 | BLOCKED | False | True | surrun_98b55100b73cb3a5952d4081 | UNDERPOWERED |
| sspec_0b99fe38aef1aab26e375a42 | trade_date_block_shuffle | 9874 | BLOCKED | False | True | surrun_cb71d15105fabe6b93de5fc7 | UNDERPOWERED |
| sspec_0b99fe38aef1aab26e375a42 | trade_date_block_shuffle | 9875 | BLOCKED | False | True | surrun_72182dbdf78a5a96276d4f2f | UNDERPOWERED |
| sspec_b2f386d7228951add40f8f58 | trade_date_block_shuffle | 9876 | BLOCKED | False | True | surrun_9eb68f457ba1996532968ece | UNDERPOWERED |
| sspec_b2f386d7228951add40f8f58 | trade_date_block_shuffle | 9877 | BLOCKED | False | True | surrun_2b615adf5140f29d2a9b3688 | UNDERPOWERED |
| sspec_b2f386d7228951add40f8f58 | trade_date_block_shuffle | 9878 | BLOCKED | False | True | surrun_9e5feac436f70d240387839f | UNDERPOWERED |
| sspec_c9347f4c8fecb525ea7bb0cb | trade_date_block_shuffle | 9879 | BLOCKED | False | True | surrun_4e04dafaaa05911a7d69e43c | UNDERPOWERED |
| sspec_c9347f4c8fecb525ea7bb0cb | trade_date_block_shuffle | 9880 | BLOCKED | False | True | surrun_fffd8e75c1131446d4045a6f | UNDERPOWERED |
| sspec_c9347f4c8fecb525ea7bb0cb | trade_date_block_shuffle | 9881 | BLOCKED | False | True | surrun_4806b605acf4ad96e1c7d08d | UNDERPOWERED |
| sspec_8ced88b02c639aad303d9ed6 | trade_date_block_shuffle | 9882 | BLOCKED | False | True | surrun_28021cdcbcfdab8b8d597477 | UNDERPOWERED |
| sspec_8ced88b02c639aad303d9ed6 | trade_date_block_shuffle | 9883 | BLOCKED | False | True | surrun_57c6dfd0b42ba08e91125b8b | UNDERPOWERED |
| sspec_8ced88b02c639aad303d9ed6 | trade_date_block_shuffle | 9884 | BLOCKED | False | True | surrun_321128e4cd81504e3f1fa78a | UNDERPOWERED |
| sspec_52fd6870c320b613b28db4da | trade_date_block_shuffle | 9885 | BLOCKED | False | True | surrun_c4c2dc4e2abae2d60931b387 | UNDERPOWERED |
| sspec_52fd6870c320b613b28db4da | trade_date_block_shuffle | 9886 | BLOCKED | False | True | surrun_a5eb537c589c0abbb6468bfd | UNDERPOWERED |
| sspec_52fd6870c320b613b28db4da | trade_date_block_shuffle | 9887 | BLOCKED | False | True | surrun_9469756890dd0023dee67a74 | UNDERPOWERED |
| sspec_4265c4aba76f54d160acdd99 | trade_date_block_shuffle | 9888 | BLOCKED | False | True | surrun_ff3cb72cc06beb1b5c18aff9 | UNDERPOWERED |
| sspec_4265c4aba76f54d160acdd99 | trade_date_block_shuffle | 9889 | BLOCKED | False | True | surrun_82e2902e5c0b74dc7a1cb4e1 | UNDERPOWERED |
| sspec_4265c4aba76f54d160acdd99 | trade_date_block_shuffle | 9890 | BLOCKED | False | True | surrun_b9b9105398a2f7fae3347e5c | UNDERPOWERED |
| sspec_a891ef6348771ff47ef91f55 | trade_date_block_shuffle | 9891 | BLOCKED | False | True | surrun_f3267d6bbab950181ca1d4e2 | UNDERPOWERED |
| sspec_a891ef6348771ff47ef91f55 | trade_date_block_shuffle | 9892 | BLOCKED | False | True | surrun_2756f8715e95eb2d4cf7a5fc | UNDERPOWERED |
| sspec_a891ef6348771ff47ef91f55 | trade_date_block_shuffle | 9893 | BLOCKED | False | True | surrun_ca3a3bae8310f714c695f684 | UNDERPOWERED |
| sspec_38921b819609131f1fedfed3 | trade_date_block_shuffle | 9894 | BLOCKED | False | True | surrun_f9bf15833f38b2d8c998acd7 | UNDERPOWERED |
| sspec_38921b819609131f1fedfed3 | trade_date_block_shuffle | 9895 | BLOCKED | False | True | surrun_01b26781c8784b43aa13e2d7 | UNDERPOWERED |
| sspec_38921b819609131f1fedfed3 | trade_date_block_shuffle | 9896 | BLOCKED | False | True | surrun_042587b84b2debc417e6709b | UNDERPOWERED |
| sspec_538e4bd64d791e63b37b8211 | trade_date_block_shuffle | 9897 | BLOCKED | False | True | surrun_723a07e4182e3dd6120a5970 | UNDERPOWERED |
| sspec_538e4bd64d791e63b37b8211 | trade_date_block_shuffle | 9898 | BLOCKED | False | True | surrun_6f31c83c8b3c0bceeaaa2962 | UNDERPOWERED |
| sspec_538e4bd64d791e63b37b8211 | trade_date_block_shuffle | 9899 | BLOCKED | False | True | surrun_6bc21f04baf6b2bc4b36f325 | UNDERPOWERED |
| sspec_bbb01bda4887680914b49dd1 | trade_date_block_shuffle | 9900 | BLOCKED | False | True | surrun_7b75177eedf391ffaeaab611 | UNDERPOWERED |
| sspec_bbb01bda4887680914b49dd1 | trade_date_block_shuffle | 9901 | BLOCKED | False | True | surrun_60f3be8327abfbaf3bad396e | UNDERPOWERED |
| sspec_bbb01bda4887680914b49dd1 | trade_date_block_shuffle | 9902 | BLOCKED | False | True | surrun_eb8aa3114f537c7a627c1637 | UNDERPOWERED |
| sspec_6207a4edc90a1eda73f9c07a | trade_date_block_shuffle | 9903 | BLOCKED | False | True | surrun_ceb74ec23d9fd6199f623285 | UNDERPOWERED |
| sspec_6207a4edc90a1eda73f9c07a | trade_date_block_shuffle | 9904 | BLOCKED | False | True | surrun_6cf5b8d04b9dc7f10510ba43 | UNDERPOWERED |
| sspec_6207a4edc90a1eda73f9c07a | trade_date_block_shuffle | 9905 | BLOCKED | False | True | surrun_5027cbf05489830cfb6071ae | UNDERPOWERED |
| sspec_7bd73bdd58c5b34fc7f858b5 | trade_date_block_shuffle | 9906 | BLOCKED | False | True | surrun_b774bc4c323d78d3e1c1323f | UNDERPOWERED |
| sspec_7bd73bdd58c5b34fc7f858b5 | trade_date_block_shuffle | 9907 | BLOCKED | False | True | surrun_6dd478515eecf89eb26a000b | UNDERPOWERED |
| sspec_7bd73bdd58c5b34fc7f858b5 | trade_date_block_shuffle | 9908 | BLOCKED | False | True | surrun_9fb11dfbb38906017394df0f | UNDERPOWERED |
| sspec_eba163cfe277594811711a81 | trade_date_block_shuffle | 9909 | BLOCKED | False | True | surrun_c89662f27843db3cec97c89f | UNDERPOWERED |
| sspec_eba163cfe277594811711a81 | trade_date_block_shuffle | 9910 | BLOCKED | False | True | surrun_299d3828c828a620fdda68f3 | UNDERPOWERED |
| sspec_eba163cfe277594811711a81 | trade_date_block_shuffle | 9911 | BLOCKED | False | True | surrun_cdfafa1ff6112c3358ecc997 | UNDERPOWERED |
| sspec_0af894479cebdd5cc89b6778 | trade_date_block_shuffle | 9912 | BLOCKED | False | True | surrun_f664d9c535299d29a122b95b | UNDERPOWERED |
| sspec_0af894479cebdd5cc89b6778 | trade_date_block_shuffle | 9913 | BLOCKED | False | True | surrun_ac26a8b0eac599da2cc793ff | UNDERPOWERED |
| sspec_0af894479cebdd5cc89b6778 | trade_date_block_shuffle | 9914 | BLOCKED | False | True | surrun_cfc6f02f03d36d4715335c85 | UNDERPOWERED |
| sspec_ff0452699f84ef333ba84253 | trade_date_block_shuffle | 9915 | BLOCKED | False | True | surrun_20a7992751386c0e83ef7779 | UNDERPOWERED |
| sspec_ff0452699f84ef333ba84253 | trade_date_block_shuffle | 9916 | BLOCKED | False | True | surrun_393ec4a927c778624f35daad | UNDERPOWERED |
| sspec_ff0452699f84ef333ba84253 | trade_date_block_shuffle | 9917 | BLOCKED | False | True | surrun_dce95c7fa586d2ad8da8670e | UNDERPOWERED |
| sspec_dc1a61174b9ee5cbab27d95c | trade_date_block_shuffle | 9918 | BLOCKED | False | True | surrun_ccf3582274abecfa2dbb75f2 | UNDERPOWERED |
| sspec_dc1a61174b9ee5cbab27d95c | trade_date_block_shuffle | 9919 | BLOCKED | False | True | surrun_c0e83ff805989c460ebd18f8 | UNDERPOWERED |
| sspec_dc1a61174b9ee5cbab27d95c | trade_date_block_shuffle | 9920 | BLOCKED | False | True | surrun_d23ecdddd5ad007de2fb172d | UNDERPOWERED |
| sspec_00550a7fe18875df0c44ce7e | trade_date_block_shuffle | 9921 | BLOCKED | False | True | surrun_0869feb769c1167b20063830 | UNDERPOWERED |
| sspec_00550a7fe18875df0c44ce7e | trade_date_block_shuffle | 9922 | BLOCKED | False | True | surrun_2faa85ca773f6ae0dd7eb13c | UNDERPOWERED |
| sspec_00550a7fe18875df0c44ce7e | trade_date_block_shuffle | 9923 | BLOCKED | False | True | surrun_abf7eea4dad1a4de65d855cb | UNDERPOWERED |
| sspec_dcb517b41a6f4b47ddda957b | trade_date_block_shuffle | 9924 | BLOCKED | False | True | surrun_ebe8b11cb2b0d9f6cf982cb5 | UNDERPOWERED |
| sspec_dcb517b41a6f4b47ddda957b | trade_date_block_shuffle | 9925 | BLOCKED | False | True | surrun_9acf54e90f42def0b508749f | UNDERPOWERED |
| sspec_dcb517b41a6f4b47ddda957b | trade_date_block_shuffle | 9926 | BLOCKED | False | True | surrun_500090105b185a3d1d85df36 | UNDERPOWERED |
| sspec_2da0ad738e06829603db55a7 | trade_date_block_shuffle | 9927 | BLOCKED | False | True | surrun_fdcf39e903f25a881c03512a | UNDERPOWERED |
| sspec_2da0ad738e06829603db55a7 | trade_date_block_shuffle | 9928 | BLOCKED | False | True | surrun_57a1648036689c35874e59d2 | UNDERPOWERED |
| sspec_2da0ad738e06829603db55a7 | trade_date_block_shuffle | 9929 | BLOCKED | False | True | surrun_a10408ccc537da9905cb9e46 | UNDERPOWERED |
| sspec_be4cd0ad733b9eedd964f43b | trade_date_block_shuffle | 9930 | BLOCKED | False | True | surrun_26360dbfb365768b90fd2a9c | UNDERPOWERED |
| sspec_be4cd0ad733b9eedd964f43b | trade_date_block_shuffle | 9931 | BLOCKED | False | True | surrun_36254eb6a3a633255b5f0951 | UNDERPOWERED |
| sspec_be4cd0ad733b9eedd964f43b | trade_date_block_shuffle | 9932 | BLOCKED | False | True | surrun_c3a2ebc57ab5647c0255faba | UNDERPOWERED |
| sspec_2ea8be2fef0c99953be058db | trade_date_block_shuffle | 9933 | BLOCKED | False | True | surrun_a5737e00db58b3a058c622d1 | UNDERPOWERED |
| sspec_2ea8be2fef0c99953be058db | trade_date_block_shuffle | 9934 | BLOCKED | False | True | surrun_8ae95d4ad75a707917614a0b | UNDERPOWERED |
| sspec_2ea8be2fef0c99953be058db | trade_date_block_shuffle | 9935 | BLOCKED | False | True | surrun_c60d6f83c9b7dfd378d0d4a6 | UNDERPOWERED |
| sspec_adda950f2882047d77c9f571 | trade_date_block_shuffle | 9936 | BLOCKED | False | True | surrun_105be4fde01b057b1e894b14 | UNDERPOWERED |
| sspec_adda950f2882047d77c9f571 | trade_date_block_shuffle | 9937 | BLOCKED | False | True | surrun_66fdd343b5be32bbf7ccc999 | UNDERPOWERED |
| sspec_adda950f2882047d77c9f571 | trade_date_block_shuffle | 9938 | BLOCKED | False | True | surrun_3345e3d923e66aca4f73db24 | UNDERPOWERED |
| sspec_e20c871270f64c22f5ee6f52 | trade_date_block_shuffle | 9939 | BLOCKED | False | True | surrun_4bae7ddb0af7ca71e0428f16 | UNDERPOWERED |
| sspec_e20c871270f64c22f5ee6f52 | trade_date_block_shuffle | 9940 | BLOCKED | False | True | surrun_b27261f96166dd4e28c349b3 | UNDERPOWERED |
| sspec_e20c871270f64c22f5ee6f52 | trade_date_block_shuffle | 9941 | BLOCKED | False | True | surrun_f23bb686ab4e401874a3f6ff | UNDERPOWERED |
| sspec_a96d2ce2d4693ffdd1835dd2 | trade_date_block_shuffle | 9942 | BLOCKED | False | True | surrun_e12c9bde0c434b80f74594c7 | UNDERPOWERED |
| sspec_a96d2ce2d4693ffdd1835dd2 | trade_date_block_shuffle | 9943 | BLOCKED | False | True | surrun_88b4304e6cd29652b1a5d3aa | UNDERPOWERED |
| sspec_a96d2ce2d4693ffdd1835dd2 | trade_date_block_shuffle | 9944 | BLOCKED | False | True | surrun_73677cccbcf05a387eb74c6a | UNDERPOWERED |
| sspec_4f15451d74f1c3e4e07cfec7 | trade_date_block_shuffle | 9945 | BLOCKED | False | True | surrun_c66c9f85bf51b16b500752d6 | UNDERPOWERED |
| sspec_4f15451d74f1c3e4e07cfec7 | trade_date_block_shuffle | 9946 | BLOCKED | False | True | surrun_e39dcf8eaaabfe297d5dbb73 | UNDERPOWERED |
| sspec_4f15451d74f1c3e4e07cfec7 | trade_date_block_shuffle | 9947 | BLOCKED | False | True | surrun_1d33743c2f78ae4186e6eca9 | UNDERPOWERED |
| sspec_a128fd7038f27f2e60a4786f | trade_date_block_shuffle | 9948 | BLOCKED | False | True | surrun_21fc374547acfcff858c3e38 | UNDERPOWERED |
| sspec_a128fd7038f27f2e60a4786f | trade_date_block_shuffle | 9949 | BLOCKED | False | True | surrun_3444e832003377d569273bac | UNDERPOWERED |
| sspec_a128fd7038f27f2e60a4786f | trade_date_block_shuffle | 9950 | BLOCKED | False | True | surrun_02db3606d00728e8ac277265 | UNDERPOWERED |
| sspec_e12267b86e680964aa44200c | trade_date_block_shuffle | 9951 | BLOCKED | False | True | surrun_6e4af9808aa0c1d594dd7012 | UNDERPOWERED |
| sspec_e12267b86e680964aa44200c | trade_date_block_shuffle | 9952 | BLOCKED | False | True | surrun_9976a553f9d93a2bbeab328f | UNDERPOWERED |
| sspec_e12267b86e680964aa44200c | trade_date_block_shuffle | 9953 | BLOCKED | False | True | surrun_21336b706a1052e2fc35e6ad | UNDERPOWERED |
| sspec_f7f60461859d208503684330 | trade_date_block_shuffle | 9954 | BLOCKED | False | True | surrun_540681d8cb88c574fc3be274 | UNDERPOWERED |
| sspec_f7f60461859d208503684330 | trade_date_block_shuffle | 9955 | BLOCKED | False | True | surrun_caa57fd4892f3b593e1a6e51 | UNDERPOWERED |
| sspec_f7f60461859d208503684330 | trade_date_block_shuffle | 9956 | BLOCKED | False | True | surrun_51ae61dc7302d4f73d2e591b | UNDERPOWERED |
| sspec_f17c0941e9d30ed073b12f61 | trade_date_block_shuffle | 9957 | BLOCKED | False | True | surrun_96bae3d448bd46391baff809 | UNDERPOWERED |
| sspec_f17c0941e9d30ed073b12f61 | trade_date_block_shuffle | 9958 | BLOCKED | False | True | surrun_0cfe9cdb4be3bad5864ebcd6 | UNDERPOWERED |
| sspec_f17c0941e9d30ed073b12f61 | trade_date_block_shuffle | 9959 | BLOCKED | False | True | surrun_fdc9afd6d5b49b0e3ff22f77 | UNDERPOWERED |
| sspec_7e79f1b5e4854cb1257cda63 | trade_date_block_bootstrap | 9960 | BLOCKED | False | True | surrun_5924a6ef492449c994dfa7a8 | UNDERPOWERED |
| sspec_7e79f1b5e4854cb1257cda63 | trade_date_block_bootstrap | 9961 | BLOCKED | False | True | surrun_acef979fc379140b39f1d429 | UNDERPOWERED |
| sspec_7e79f1b5e4854cb1257cda63 | trade_date_block_bootstrap | 9962 | BLOCKED | False | True | surrun_219d6a0e700f3ceaf40f3de6 | UNDERPOWERED |
| sspec_1ad21ea07e54b70a3c22ca54 | trade_date_block_bootstrap | 9963 | BLOCKED | False | True | surrun_50b7d65510812a552ebbf7e3 | UNDERPOWERED |
| sspec_1ad21ea07e54b70a3c22ca54 | trade_date_block_bootstrap | 9964 | BLOCKED | False | True | surrun_18b9ec0472da90b6a46d4ba4 | UNDERPOWERED |
| sspec_1ad21ea07e54b70a3c22ca54 | trade_date_block_bootstrap | 9965 | BLOCKED | False | True | surrun_6f682cbe3dc059c5566a00b6 | UNDERPOWERED |
| sspec_93ae072de5e1947d33a9d0dc | trade_date_block_bootstrap | 9966 | BLOCKED | False | True | surrun_41afb95f5bfaf26c0fd0f88c | UNDERPOWERED |
| sspec_93ae072de5e1947d33a9d0dc | trade_date_block_bootstrap | 9967 | BLOCKED | False | True | surrun_cccf60cfde0fbe8278556816 | UNDERPOWERED |
| sspec_93ae072de5e1947d33a9d0dc | trade_date_block_bootstrap | 9968 | BLOCKED | False | True | surrun_eca654e05a5ed72a13a84589 | UNDERPOWERED |
| sspec_f55b84e46d44016a0ead37fd | trade_date_block_bootstrap | 9969 | BLOCKED | False | True | surrun_e6e0740aba3ae0d260a3b0cb | UNDERPOWERED |
| sspec_f55b84e46d44016a0ead37fd | trade_date_block_bootstrap | 9970 | BLOCKED | False | True | surrun_afe3ab66bf6a78a65d8edff8 | UNDERPOWERED |
| sspec_f55b84e46d44016a0ead37fd | trade_date_block_bootstrap | 9971 | BLOCKED | False | True | surrun_75c8ef9e43ae933b998bed0e | UNDERPOWERED |
| sspec_8998644a516c93a24b3ef787 | trade_date_block_bootstrap | 9972 | BLOCKED | False | True | surrun_d20c2d648525b38caf6a48b6 | UNDERPOWERED |
| sspec_8998644a516c93a24b3ef787 | trade_date_block_bootstrap | 9973 | BLOCKED | False | True | surrun_c1d902733856ccfd1cf96de6 | UNDERPOWERED |
| sspec_8998644a516c93a24b3ef787 | trade_date_block_bootstrap | 9974 | BLOCKED | False | True | surrun_0f489a0b11c0c13fadf03319 | UNDERPOWERED |
| sspec_3d8d87ebd27287fe2aac314a | trade_date_block_bootstrap | 9975 | BLOCKED | False | True | surrun_aa835534e78411a2222ee652 | UNDERPOWERED |
| sspec_3d8d87ebd27287fe2aac314a | trade_date_block_bootstrap | 9976 | BLOCKED | False | True | surrun_65596b508b43cda6c0e1c4c7 | UNDERPOWERED |
| sspec_3d8d87ebd27287fe2aac314a | trade_date_block_bootstrap | 9977 | BLOCKED | False | True | surrun_5975741d0d57c9bfcd91e324 | UNDERPOWERED |
| sspec_7e25b1b59f9442607d51c9b0 | trade_date_block_bootstrap | 9978 | BLOCKED | False | True | surrun_7c7361edff98c93e0846aa12 | UNDERPOWERED |
| sspec_7e25b1b59f9442607d51c9b0 | trade_date_block_bootstrap | 9979 | BLOCKED | False | True | surrun_bd567175cb6c552eed226e75 | UNDERPOWERED |
| sspec_7e25b1b59f9442607d51c9b0 | trade_date_block_bootstrap | 9980 | BLOCKED | False | True | surrun_8047eb3b44fe98cb50815e6d | UNDERPOWERED |
| sspec_1a30430408744f9767cadb44 | trade_date_block_bootstrap | 9981 | BLOCKED | False | True | surrun_4a6e7ee905f239341044bce7 | UNDERPOWERED |
| sspec_1a30430408744f9767cadb44 | trade_date_block_bootstrap | 9982 | BLOCKED | False | True | surrun_bfd7b2a20f1bdf36c69fd620 | UNDERPOWERED |
| sspec_1a30430408744f9767cadb44 | trade_date_block_bootstrap | 9983 | BLOCKED | False | True | surrun_9040ba59bf12d6c7331a2cd3 | UNDERPOWERED |
| sspec_ffb23ccd6863fdef6033a724 | trade_date_block_bootstrap | 9984 | BLOCKED | False | True | surrun_8183ae91ac5440081e1b5648 | UNDERPOWERED |
| sspec_ffb23ccd6863fdef6033a724 | trade_date_block_bootstrap | 9985 | BLOCKED | False | True | surrun_c646fcc7d2bb139b0d363b84 | UNDERPOWERED |
| sspec_ffb23ccd6863fdef6033a724 | trade_date_block_bootstrap | 9986 | BLOCKED | False | True | surrun_385f1a24e0ee6920e9479ebf | UNDERPOWERED |
| sspec_8a4da6ebf51436aa38ad6907 | trade_date_block_bootstrap | 9987 | BLOCKED | False | True | surrun_be488c8ccd0fc1703f3db9ce | UNDERPOWERED |
| sspec_8a4da6ebf51436aa38ad6907 | trade_date_block_bootstrap | 9988 | BLOCKED | False | True | surrun_970665e80d1f83da2d4e9d62 | UNDERPOWERED |
| sspec_8a4da6ebf51436aa38ad6907 | trade_date_block_bootstrap | 9989 | BLOCKED | False | True | surrun_419aaf712730703b9bbad11c | UNDERPOWERED |
| sspec_a717397d0e0a7cb384b5b956 | trade_date_block_bootstrap | 9990 | BLOCKED | False | True | surrun_40f796a8e4c07246f8895509 | UNDERPOWERED |
| sspec_a717397d0e0a7cb384b5b956 | trade_date_block_bootstrap | 9991 | BLOCKED | False | True | surrun_454de731d34f8a315c828a0b | UNDERPOWERED |
| sspec_a717397d0e0a7cb384b5b956 | trade_date_block_bootstrap | 9992 | BLOCKED | False | True | surrun_074920661b4db735dbb29ae0 | UNDERPOWERED |
| sspec_cb719518b6985d25d6ccd08c | trade_date_block_bootstrap | 9993 | BLOCKED | False | True | surrun_2a6e3f608b6cc2d466771f53 | UNDERPOWERED |
| sspec_cb719518b6985d25d6ccd08c | trade_date_block_bootstrap | 9994 | BLOCKED | False | True | surrun_7b9504c0b04c31593d3c02e2 | UNDERPOWERED |
| sspec_cb719518b6985d25d6ccd08c | trade_date_block_bootstrap | 9995 | BLOCKED | False | True | surrun_00b97639da5a1ffd47b4cce4 | UNDERPOWERED |
| sspec_8dd3be627defa4bdbd9d86ec | trade_date_block_bootstrap | 9996 | BLOCKED | False | True | surrun_192ef7d2a9102dbe632605a2 | UNDERPOWERED |
| sspec_8dd3be627defa4bdbd9d86ec | trade_date_block_bootstrap | 9997 | BLOCKED | False | True | surrun_e97a0f7bfa7b2b16c69565ba | UNDERPOWERED |
| sspec_8dd3be627defa4bdbd9d86ec | trade_date_block_bootstrap | 9998 | BLOCKED | False | True | surrun_c3b6455c5f61315dbe64229d | UNDERPOWERED |
| sspec_520f127a1734d90457cd4442 | trade_date_block_bootstrap | 9999 | BLOCKED | False | True | surrun_08329eb92a1903477d4e1c89 | UNDERPOWERED |
| sspec_520f127a1734d90457cd4442 | trade_date_block_bootstrap | 10000 | BLOCKED | False | True | surrun_61a27f91571569e3f79abd43 | UNDERPOWERED |
| sspec_520f127a1734d90457cd4442 | trade_date_block_bootstrap | 10001 | BLOCKED | False | True | surrun_67249a666a450cc61d14940f | UNDERPOWERED |
| sspec_9793f7bfa9851ece64032bf8 | trade_date_block_bootstrap | 10002 | BLOCKED | False | True | surrun_2e6ac06bfcc97d7815fbbc3f | UNDERPOWERED |
| sspec_9793f7bfa9851ece64032bf8 | trade_date_block_bootstrap | 10003 | BLOCKED | False | True | surrun_fe898d1f1568780f1eb23e90 | UNDERPOWERED |
| sspec_9793f7bfa9851ece64032bf8 | trade_date_block_bootstrap | 10004 | BLOCKED | False | True | surrun_9b79a310f487f2c7301686a1 | UNDERPOWERED |
| sspec_41a7dcd4f4e4cffffdaf8053 | trade_date_block_bootstrap | 10005 | BLOCKED | False | True | surrun_a9c872f4ea09f65acfa1464c | UNDERPOWERED |
| sspec_41a7dcd4f4e4cffffdaf8053 | trade_date_block_bootstrap | 10006 | BLOCKED | False | True | surrun_d718519217b7a1216b5e9858 | UNDERPOWERED |
| sspec_41a7dcd4f4e4cffffdaf8053 | trade_date_block_bootstrap | 10007 | BLOCKED | False | True | surrun_fa3e507d0182e8011148730b | UNDERPOWERED |
| sspec_6befecec7cfb7f2c5b3fd8c7 | trade_date_block_bootstrap | 10008 | BLOCKED | False | True | surrun_cf84fc982f27b2367fdaea53 | UNDERPOWERED |
| sspec_6befecec7cfb7f2c5b3fd8c7 | trade_date_block_bootstrap | 10009 | BLOCKED | False | True | surrun_fba10750fb0faea259d48a6a | UNDERPOWERED |
| sspec_6befecec7cfb7f2c5b3fd8c7 | trade_date_block_bootstrap | 10010 | BLOCKED | False | True | surrun_8acb2033056ef3e3745646fb | UNDERPOWERED |
| sspec_867c79cf4e938d9257746fb0 | trade_date_block_bootstrap | 10011 | BLOCKED | False | True | surrun_5247cfe1985f92396ad11932 | UNDERPOWERED |
| sspec_867c79cf4e938d9257746fb0 | trade_date_block_bootstrap | 10012 | BLOCKED | False | True | surrun_058432e44788a076d3a90441 | UNDERPOWERED |
| sspec_867c79cf4e938d9257746fb0 | trade_date_block_bootstrap | 10013 | BLOCKED | False | True | surrun_5adf68650ca139a120f1bfb3 | UNDERPOWERED |
| sspec_5594a8f3d12c767aefcf73ce | trade_date_block_bootstrap | 10014 | BLOCKED | False | True | surrun_018d824345ad0535f3c0c3ab | UNDERPOWERED |
| sspec_5594a8f3d12c767aefcf73ce | trade_date_block_bootstrap | 10015 | BLOCKED | False | True | surrun_796e74770353314d2b79ee80 | UNDERPOWERED |
| sspec_5594a8f3d12c767aefcf73ce | trade_date_block_bootstrap | 10016 | BLOCKED | False | True | surrun_58d27b8199b0853116fc91cd | UNDERPOWERED |
| sspec_e1ac3cb2e0c7e222be6e0f58 | trade_date_block_bootstrap | 10017 | BLOCKED | False | True | surrun_1343b6c305db61d8bc527811 | UNDERPOWERED |
| sspec_e1ac3cb2e0c7e222be6e0f58 | trade_date_block_bootstrap | 10018 | BLOCKED | False | True | surrun_364d26f87652058e750a17c2 | UNDERPOWERED |
| sspec_e1ac3cb2e0c7e222be6e0f58 | trade_date_block_bootstrap | 10019 | BLOCKED | False | True | surrun_7d165440d756116c037bfb86 | UNDERPOWERED |
| sspec_c2cca46451da082747ccf894 | trade_date_block_bootstrap | 10020 | BLOCKED | False | True | surrun_844a01765d6784345e8177c6 | UNDERPOWERED |
| sspec_c2cca46451da082747ccf894 | trade_date_block_bootstrap | 10021 | BLOCKED | False | True | surrun_e6cabfeb2d0f4764474375b3 | UNDERPOWERED |
| sspec_c2cca46451da082747ccf894 | trade_date_block_bootstrap | 10022 | BLOCKED | False | True | surrun_8b382b3341cfcaa363a5323a | UNDERPOWERED |
| sspec_c025e8db6d95f0475f7defb1 | trade_date_block_bootstrap | 10023 | BLOCKED | False | True | surrun_fa6f9bd86172b394b0d0ba0d | UNDERPOWERED |
| sspec_c025e8db6d95f0475f7defb1 | trade_date_block_bootstrap | 10024 | BLOCKED | False | True | surrun_b29fa181f29323008715be4d | UNDERPOWERED |
| sspec_c025e8db6d95f0475f7defb1 | trade_date_block_bootstrap | 10025 | BLOCKED | False | True | surrun_7211d26ba6ed188c043060aa | UNDERPOWERED |
| sspec_d80fc74961ac9aca6bad11e7 | trade_date_block_bootstrap | 10026 | BLOCKED | False | True | surrun_1e598c27e20db2783cffcf99 | UNDERPOWERED |
| sspec_d80fc74961ac9aca6bad11e7 | trade_date_block_bootstrap | 10027 | BLOCKED | False | True | surrun_b71b185d56ba8e6c6f9c0d16 | UNDERPOWERED |
| sspec_d80fc74961ac9aca6bad11e7 | trade_date_block_bootstrap | 10028 | BLOCKED | False | True | surrun_fc3f41a053a90fe34847c676 | UNDERPOWERED |
| sspec_91a919b77f6f8220213f68cf | trade_date_block_bootstrap | 10029 | BLOCKED | False | True | surrun_7beb041623812cafa9b40c0f | UNDERPOWERED |
| sspec_91a919b77f6f8220213f68cf | trade_date_block_bootstrap | 10030 | BLOCKED | False | True | surrun_f16f592aa055fb9577cd0548 | UNDERPOWERED |
| sspec_91a919b77f6f8220213f68cf | trade_date_block_bootstrap | 10031 | BLOCKED | False | True | surrun_4138e20b6262ee32fa0eec91 | UNDERPOWERED |
| sspec_70756efa7cc952ce60d7854e | trade_date_block_bootstrap | 10032 | BLOCKED | False | True | surrun_dada38e82042fded24adee6f | UNDERPOWERED |
| sspec_70756efa7cc952ce60d7854e | trade_date_block_bootstrap | 10033 | BLOCKED | False | True | surrun_683f42e5861c7415e32c6b61 | UNDERPOWERED |
| sspec_70756efa7cc952ce60d7854e | trade_date_block_bootstrap | 10034 | BLOCKED | False | True | surrun_442a0d1b1293052f823c1e43 | UNDERPOWERED |
| sspec_c4ceba27c93f33eedce86f50 | trade_date_block_bootstrap | 10035 | BLOCKED | False | True | surrun_27986524f08dac4a7f55d49b | UNDERPOWERED |
| sspec_c4ceba27c93f33eedce86f50 | trade_date_block_bootstrap | 10036 | BLOCKED | False | True | surrun_31039395c182279265ee09c9 | UNDERPOWERED |
| sspec_c4ceba27c93f33eedce86f50 | trade_date_block_bootstrap | 10037 | BLOCKED | False | True | surrun_7b509b3e351114e39773c0ff | UNDERPOWERED |
| sspec_f314f2efd00d36d1889d00fe | trade_date_block_bootstrap | 10038 | BLOCKED | False | True | surrun_84a91a63bf2284268f9bb4f1 | UNDERPOWERED |
| sspec_f314f2efd00d36d1889d00fe | trade_date_block_bootstrap | 10039 | BLOCKED | False | True | surrun_2edfd69a48799dc87ab1ba5e | UNDERPOWERED |
| sspec_f314f2efd00d36d1889d00fe | trade_date_block_bootstrap | 10040 | BLOCKED | False | True | surrun_5b02484c87f0579d0ee8d2b6 | UNDERPOWERED |
| sspec_fba1a8693a8229188942c231 | trade_date_block_bootstrap | 10041 | BLOCKED | False | True | surrun_442b7b5668c24c3a65766b50 | UNDERPOWERED |
| sspec_fba1a8693a8229188942c231 | trade_date_block_bootstrap | 10042 | BLOCKED | False | True | surrun_06f69eef6dcbd6b0b50116ac | UNDERPOWERED |
| sspec_fba1a8693a8229188942c231 | trade_date_block_bootstrap | 10043 | BLOCKED | False | True | surrun_c8110a070cbca0ae349ab9e1 | UNDERPOWERED |
| sspec_a7e9731d3ef8c37d5a880801 | trade_date_block_bootstrap | 10044 | BLOCKED | False | True | surrun_c82c0f80d1581fcf90fa6a5c | UNDERPOWERED |
| sspec_a7e9731d3ef8c37d5a880801 | trade_date_block_bootstrap | 10045 | BLOCKED | False | True | surrun_5f0cfcaad8fc0e988ed13c32 | UNDERPOWERED |
| sspec_a7e9731d3ef8c37d5a880801 | trade_date_block_bootstrap | 10046 | BLOCKED | False | True | surrun_b53bde6ac9cf8fe912973ea1 | UNDERPOWERED |
| sspec_3fd49fca02465bd9a11a2f23 | trade_date_block_bootstrap | 10047 | BLOCKED | False | True | surrun_615c9c5da2ccf8be643153ee | UNDERPOWERED |
| sspec_3fd49fca02465bd9a11a2f23 | trade_date_block_bootstrap | 10048 | BLOCKED | False | True | surrun_53c06297e70c16e3dd97439e | UNDERPOWERED |
| sspec_3fd49fca02465bd9a11a2f23 | trade_date_block_bootstrap | 10049 | BLOCKED | False | True | surrun_d9e8e35634bf8b08ecf8dd99 | UNDERPOWERED |
| sspec_5cc9cbcb196e6baa32920952 | trade_date_block_bootstrap | 10050 | BLOCKED | False | True | surrun_1b9ecddd920f54c8223ac998 | UNDERPOWERED |
| sspec_5cc9cbcb196e6baa32920952 | trade_date_block_bootstrap | 10051 | BLOCKED | False | True | surrun_58e7c057c4a8089e070beb89 | UNDERPOWERED |
| sspec_5cc9cbcb196e6baa32920952 | trade_date_block_bootstrap | 10052 | BLOCKED | False | True | surrun_b4d642175a3431080c35a392 | UNDERPOWERED |
| sspec_8ada06420b84793baca8c62f | trade_date_block_bootstrap | 10053 | BLOCKED | False | True | surrun_564280a4077eab50c9b64375 | UNDERPOWERED |
| sspec_8ada06420b84793baca8c62f | trade_date_block_bootstrap | 10054 | BLOCKED | False | True | surrun_b64a23260fd943b887325d19 | UNDERPOWERED |
| sspec_8ada06420b84793baca8c62f | trade_date_block_bootstrap | 10055 | BLOCKED | False | True | surrun_003d220cdb03e5852a8af461 | UNDERPOWERED |
| sspec_9987f684a025b26d844db5ed | trade_date_block_bootstrap | 10056 | BLOCKED | False | True | surrun_2dabbc13b25a3468d18dc62d | UNDERPOWERED |
| sspec_9987f684a025b26d844db5ed | trade_date_block_bootstrap | 10057 | BLOCKED | False | True | surrun_6455b95e27b8f76305cdc398 | UNDERPOWERED |
| sspec_9987f684a025b26d844db5ed | trade_date_block_bootstrap | 10058 | BLOCKED | False | True | surrun_94eb1c69e67d9c19c82a7fca | UNDERPOWERED |
| sspec_84f839dfa7372cdeffac6257 | trade_date_block_bootstrap | 10059 | BLOCKED | False | True | surrun_45bdfd3c84498931b03f074d | UNDERPOWERED |
| sspec_84f839dfa7372cdeffac6257 | trade_date_block_bootstrap | 10060 | BLOCKED | False | True | surrun_928cc95fb5b351c304650541 | UNDERPOWERED |
| sspec_84f839dfa7372cdeffac6257 | trade_date_block_bootstrap | 10061 | BLOCKED | False | True | surrun_89da38a6742432118decf79b | UNDERPOWERED |
| sspec_0afcbe810bd46b05ae02b19c | trade_date_block_bootstrap | 10062 | BLOCKED | False | True | surrun_7dd3461d57823d7c49a3c9bf | UNDERPOWERED |
| sspec_0afcbe810bd46b05ae02b19c | trade_date_block_bootstrap | 10063 | BLOCKED | False | True | surrun_828fbfa5ee5d154258f8ffe3 | UNDERPOWERED |
| sspec_0afcbe810bd46b05ae02b19c | trade_date_block_bootstrap | 10064 | BLOCKED | False | True | surrun_d1426ecbd8a9cb521a6106d2 | UNDERPOWERED |
| sspec_8d0db05ad7c58c4643fe077b | trade_date_block_bootstrap | 10065 | BLOCKED | False | True | surrun_32774c7c8016d261c5ff4537 | UNDERPOWERED |
| sspec_8d0db05ad7c58c4643fe077b | trade_date_block_bootstrap | 10066 | BLOCKED | False | True | surrun_6d066df52d68581a8e4992d4 | UNDERPOWERED |
| sspec_8d0db05ad7c58c4643fe077b | trade_date_block_bootstrap | 10067 | BLOCKED | False | True | surrun_f93cad4acfd69140890fde5b | UNDERPOWERED |
| sspec_d7f40557b1d8042fbdc43bed | trade_date_block_bootstrap | 10068 | BLOCKED | False | True | surrun_a6cdf0a5a1cc3e668211d73d | UNDERPOWERED |
| sspec_d7f40557b1d8042fbdc43bed | trade_date_block_bootstrap | 10069 | BLOCKED | False | True | surrun_535af1febf75f46a54aaf0ba | UNDERPOWERED |
| sspec_d7f40557b1d8042fbdc43bed | trade_date_block_bootstrap | 10070 | BLOCKED | False | True | surrun_eb9988d0595aa19c442a1dc4 | UNDERPOWERED |
| sspec_05acd70e6de784ddf227f5eb | trade_date_block_bootstrap | 10071 | BLOCKED | False | True | surrun_572a441ddec39f01f0436b5b | UNDERPOWERED |
| sspec_05acd70e6de784ddf227f5eb | trade_date_block_bootstrap | 10072 | BLOCKED | False | True | surrun_01f8d7a99d4c21c4352554fb | UNDERPOWERED |
| sspec_05acd70e6de784ddf227f5eb | trade_date_block_bootstrap | 10073 | BLOCKED | False | True | surrun_7d1b521dda8ba8b8380072cb | UNDERPOWERED |
| sspec_87e724c7e9377b33803ae628 | trade_date_block_bootstrap | 10074 | BLOCKED | False | True | surrun_5f86173132ce5b4880fd4f8c | UNDERPOWERED |
| sspec_87e724c7e9377b33803ae628 | trade_date_block_bootstrap | 10075 | BLOCKED | False | True | surrun_9abb001adba8f85ab79339fb | UNDERPOWERED |
| sspec_87e724c7e9377b33803ae628 | trade_date_block_bootstrap | 10076 | BLOCKED | False | True | surrun_f32dc1409e027853ace3fce0 | UNDERPOWERED |
| sspec_f9faa8f59f3131a1e51a7550 | trade_date_block_bootstrap | 10077 | BLOCKED | False | True | surrun_20cc062442476b0283b85164 | UNDERPOWERED |
| sspec_f9faa8f59f3131a1e51a7550 | trade_date_block_bootstrap | 10078 | BLOCKED | False | True | surrun_ddfe57aea33f84f48ac70e01 | UNDERPOWERED |
| sspec_f9faa8f59f3131a1e51a7550 | trade_date_block_bootstrap | 10079 | BLOCKED | False | True | surrun_8cce720ed0efd6e341d91515 | UNDERPOWERED |
| sspec_5a135cae15ed881f04ae6fa5 | trade_date_block_bootstrap | 10080 | BLOCKED | False | True | surrun_bd0290e9b57e732ac66b9c07 | UNDERPOWERED |
| sspec_5a135cae15ed881f04ae6fa5 | trade_date_block_bootstrap | 10081 | BLOCKED | False | True | surrun_b3e2f4dbca621e18deb48662 | UNDERPOWERED |
| sspec_5a135cae15ed881f04ae6fa5 | trade_date_block_bootstrap | 10082 | BLOCKED | False | True | surrun_99d43a7560eeeb08d84f4d68 | UNDERPOWERED |
| sspec_72d581628d90f8918dac1e47 | trade_date_block_bootstrap | 10083 | BLOCKED | False | True | surrun_a7f7fa58a4f6b9055946473c | UNDERPOWERED |
| sspec_72d581628d90f8918dac1e47 | trade_date_block_bootstrap | 10084 | BLOCKED | False | True | surrun_a2d38f0cf76e95969b70c3fb | UNDERPOWERED |
| sspec_72d581628d90f8918dac1e47 | trade_date_block_bootstrap | 10085 | BLOCKED | False | True | surrun_a9edd6181416093e2e762f77 | UNDERPOWERED |
| sspec_8022f2c052c5a2dd40bd56bd | trade_date_block_bootstrap | 10086 | BLOCKED | False | True | surrun_a5d8b25026b42c5861635208 | UNDERPOWERED |
| sspec_8022f2c052c5a2dd40bd56bd | trade_date_block_bootstrap | 10087 | BLOCKED | False | True | surrun_1e98d2f84811e0fd8fe090cc | UNDERPOWERED |
| sspec_8022f2c052c5a2dd40bd56bd | trade_date_block_bootstrap | 10088 | BLOCKED | False | True | surrun_00e6c1980c1500f39cde6dec | UNDERPOWERED |
| sspec_c64d85180ea048aa542b734a | trade_date_block_bootstrap | 10089 | BLOCKED | False | True | surrun_cedee1bb0ed5a39d7d126da2 | UNDERPOWERED |
| sspec_c64d85180ea048aa542b734a | trade_date_block_bootstrap | 10090 | BLOCKED | False | True | surrun_4d1695bc564babd387a57282 | UNDERPOWERED |
| sspec_c64d85180ea048aa542b734a | trade_date_block_bootstrap | 10091 | BLOCKED | False | True | surrun_3dc32e2f97c3c90272a02c4a | UNDERPOWERED |
| sspec_3655e6865a834c8dead47c06 | trade_date_block_bootstrap | 10092 | BLOCKED | False | True | surrun_095f951c70d16948e7f49600 | UNDERPOWERED |
| sspec_3655e6865a834c8dead47c06 | trade_date_block_bootstrap | 10093 | BLOCKED | False | True | surrun_4cac9f0f29eb89fdac1258ce | UNDERPOWERED |
| sspec_3655e6865a834c8dead47c06 | trade_date_block_bootstrap | 10094 | BLOCKED | False | True | surrun_d8f250a61732b4ab3eeadc2b | UNDERPOWERED |
| sspec_ef5252b2cab7faab1a15ad15 | trade_date_block_bootstrap | 10095 | BLOCKED | False | True | surrun_1c50d39dabe61822c736cb0c | UNDERPOWERED |
| sspec_ef5252b2cab7faab1a15ad15 | trade_date_block_bootstrap | 10096 | BLOCKED | False | True | surrun_51c563941c6cd3867236c6ba | UNDERPOWERED |
| sspec_ef5252b2cab7faab1a15ad15 | trade_date_block_bootstrap | 10097 | BLOCKED | False | True | surrun_971582e8d666631611735762 | UNDERPOWERED |
| sspec_83bc285f4ff066119a9600cb | trade_date_block_bootstrap | 10098 | BLOCKED | False | True | surrun_23e95ed23a041032806738cb | UNDERPOWERED |
| sspec_83bc285f4ff066119a9600cb | trade_date_block_bootstrap | 10099 | BLOCKED | False | True | surrun_fe8eb675203087109360c907 | UNDERPOWERED |
| sspec_83bc285f4ff066119a9600cb | trade_date_block_bootstrap | 10100 | BLOCKED | False | True | surrun_e985f7099f66015c5123535d | UNDERPOWERED |
| sspec_391c5ea571770ece430c303a | trade_date_block_bootstrap | 10101 | BLOCKED | False | True | surrun_1399101de5af030870cd0dd8 | UNDERPOWERED |
| sspec_391c5ea571770ece430c303a | trade_date_block_bootstrap | 10102 | BLOCKED | False | True | surrun_b5e07723451835aca234c984 | UNDERPOWERED |
| sspec_391c5ea571770ece430c303a | trade_date_block_bootstrap | 10103 | BLOCKED | False | True | surrun_aca310006f43a5d9e9f7f345 | UNDERPOWERED |
| sspec_35729e0c9b8ada663b8becb8 | trade_date_block_bootstrap | 10104 | BLOCKED | False | True | surrun_2f1029fc3130f1148a7c6351 | UNDERPOWERED |
| sspec_35729e0c9b8ada663b8becb8 | trade_date_block_bootstrap | 10105 | BLOCKED | False | True | surrun_4d854ea1e03f7b2f0f73c760 | UNDERPOWERED |
| sspec_35729e0c9b8ada663b8becb8 | trade_date_block_bootstrap | 10106 | BLOCKED | False | True | surrun_173caa7eeb28109e361b8a88 | UNDERPOWERED |
| sspec_4d6094e489ece633dfdffd1c | trade_date_block_bootstrap | 10107 | BLOCKED | False | True | surrun_b1923788eda37c2ce86f19f8 | UNDERPOWERED |
| sspec_4d6094e489ece633dfdffd1c | trade_date_block_bootstrap | 10108 | BLOCKED | False | True | surrun_47137f4edc08c02436393e47 | UNDERPOWERED |
| sspec_4d6094e489ece633dfdffd1c | trade_date_block_bootstrap | 10109 | BLOCKED | False | True | surrun_86fd2294258f157ff575ad27 | UNDERPOWERED |
| sspec_fef006f9cc9e1213b8236939 | trade_date_block_bootstrap | 10110 | BLOCKED | False | True | surrun_b28db9b4fc59ecd26abd2fef | UNDERPOWERED |
| sspec_fef006f9cc9e1213b8236939 | trade_date_block_bootstrap | 10111 | BLOCKED | False | True | surrun_8efaa957f23fe1535ce20ffe | UNDERPOWERED |
| sspec_fef006f9cc9e1213b8236939 | trade_date_block_bootstrap | 10112 | BLOCKED | False | True | surrun_22b89f54aa77a3b2491cabd0 | UNDERPOWERED |
| sspec_d5ff5892990f8e4e9677b86a | trade_date_block_bootstrap | 10113 | BLOCKED | False | True | surrun_11c51353a1f35e7218f8c2b6 | UNDERPOWERED |
| sspec_d5ff5892990f8e4e9677b86a | trade_date_block_bootstrap | 10114 | BLOCKED | False | True | surrun_65c1d4d86ca6e005fd74977e | UNDERPOWERED |
| sspec_d5ff5892990f8e4e9677b86a | trade_date_block_bootstrap | 10115 | BLOCKED | False | True | surrun_a90025a43692b0fcfcc369ad | UNDERPOWERED |
| sspec_6cab22ffd94a58f5eee335b7 | trade_date_block_bootstrap | 10116 | BLOCKED | False | True | surrun_b7246f16b7f42e3d42ce6cd7 | UNDERPOWERED |
| sspec_6cab22ffd94a58f5eee335b7 | trade_date_block_bootstrap | 10117 | BLOCKED | False | True | surrun_89539ea160c7e5d0d3d446a9 | UNDERPOWERED |
| sspec_6cab22ffd94a58f5eee335b7 | trade_date_block_bootstrap | 10118 | BLOCKED | False | True | surrun_60ca2bbfe6c9bf1b50eafec0 | UNDERPOWERED |
| sspec_db017ceb7b249fd02c3109e4 | trade_date_block_bootstrap | 10119 | BLOCKED | False | True | surrun_a5e226f8c46eaad72db4abba | UNDERPOWERED |
| sspec_db017ceb7b249fd02c3109e4 | trade_date_block_bootstrap | 10120 | BLOCKED | False | True | surrun_9da7e7af096a41d5c80f8b82 | UNDERPOWERED |
| sspec_db017ceb7b249fd02c3109e4 | trade_date_block_bootstrap | 10121 | BLOCKED | False | True | surrun_9e8fdd42d9de9319bbf62501 | UNDERPOWERED |
| sspec_167bac07abdbb940c692d3f4 | trade_date_block_bootstrap | 10122 | BLOCKED | False | True | surrun_cf74ee91f418e4a1575cc029 | UNDERPOWERED |
| sspec_167bac07abdbb940c692d3f4 | trade_date_block_bootstrap | 10123 | BLOCKED | False | True | surrun_f6a350b66d86ce2e5029484d | UNDERPOWERED |
| sspec_167bac07abdbb940c692d3f4 | trade_date_block_bootstrap | 10124 | BLOCKED | False | True | surrun_a4d022586a9b6a07ac8636e7 | UNDERPOWERED |
| sspec_c7564368c843e9180f3b9c5d | trade_date_block_bootstrap | 10125 | BLOCKED | False | True | surrun_1478e714d5a667ca86d4eb10 | UNDERPOWERED |
| sspec_c7564368c843e9180f3b9c5d | trade_date_block_bootstrap | 10126 | BLOCKED | False | True | surrun_24d49b80fee207a5541c80a9 | UNDERPOWERED |
| sspec_c7564368c843e9180f3b9c5d | trade_date_block_bootstrap | 10127 | BLOCKED | False | True | surrun_9c70ee1d0a014b02f760558d | UNDERPOWERED |
| sspec_64e18de1ab7562b175c5abdf | trade_date_block_bootstrap | 10128 | BLOCKED | False | True | surrun_6a0e470f1324d9e8d9e2676b | UNDERPOWERED |
| sspec_64e18de1ab7562b175c5abdf | trade_date_block_bootstrap | 10129 | BLOCKED | False | True | surrun_b05824a81181f2c275268228 | UNDERPOWERED |
| sspec_64e18de1ab7562b175c5abdf | trade_date_block_bootstrap | 10130 | BLOCKED | False | True | surrun_01948b83a1e40b96fd63d215 | UNDERPOWERED |
| sspec_2a25fc4b4ea0e424771ccc96 | trade_date_block_bootstrap | 10131 | BLOCKED | False | True | surrun_c91554b481c8a2b54cc1be8c | UNDERPOWERED |
| sspec_2a25fc4b4ea0e424771ccc96 | trade_date_block_bootstrap | 10132 | BLOCKED | False | True | surrun_06a23c535bf9220263fc97b4 | UNDERPOWERED |
| sspec_2a25fc4b4ea0e424771ccc96 | trade_date_block_bootstrap | 10133 | BLOCKED | False | True | surrun_58dde45ebb0d9e0abddfca8e | UNDERPOWERED |
| sspec_665b44b6bb64c6c524834096 | trade_date_block_bootstrap | 10134 | BLOCKED | False | True | surrun_b9cccad5a87a2e8f98ea496a | UNDERPOWERED |
| sspec_665b44b6bb64c6c524834096 | trade_date_block_bootstrap | 10135 | BLOCKED | False | True | surrun_19c3a0e50429fa20b988040e | UNDERPOWERED |
| sspec_665b44b6bb64c6c524834096 | trade_date_block_bootstrap | 10136 | BLOCKED | False | True | surrun_f9a2b12d044ad7384433e0b4 | UNDERPOWERED |
| sspec_c589d1eed7e4d6323b05b9c2 | trade_date_block_bootstrap | 10137 | BLOCKED | False | True | surrun_f7c948ff6bda09b15722b5af | UNDERPOWERED |
| sspec_c589d1eed7e4d6323b05b9c2 | trade_date_block_bootstrap | 10138 | BLOCKED | False | True | surrun_b909ca29f690a649c75d6b55 | UNDERPOWERED |
| sspec_c589d1eed7e4d6323b05b9c2 | trade_date_block_bootstrap | 10139 | BLOCKED | False | True | surrun_4d375aaf3cc05d1d566c4dba | UNDERPOWERED |
| sspec_b71b3b2357dbb70f673c18fc | trade_date_block_bootstrap | 10140 | BLOCKED | False | True | surrun_a87f59bef02d4d8c669e76b0 | UNDERPOWERED |
| sspec_b71b3b2357dbb70f673c18fc | trade_date_block_bootstrap | 10141 | BLOCKED | False | True | surrun_24b039d3a1c17d4349966f95 | UNDERPOWERED |
| sspec_b71b3b2357dbb70f673c18fc | trade_date_block_bootstrap | 10142 | BLOCKED | False | True | surrun_48f49b308c99bf42d2dc21da | UNDERPOWERED |
| sspec_601a6336820a94d988b97648 | trade_date_block_bootstrap | 10143 | BLOCKED | False | True | surrun_e31f2e8575f01eb0eb5b0cb1 | UNDERPOWERED |
| sspec_601a6336820a94d988b97648 | trade_date_block_bootstrap | 10144 | BLOCKED | False | True | surrun_755d481cc29e6eee8da7c5b8 | UNDERPOWERED |
| sspec_601a6336820a94d988b97648 | trade_date_block_bootstrap | 10145 | BLOCKED | False | True | surrun_46a9af1f8f23dce1f6ade21f | UNDERPOWERED |
| sspec_b2481e16b39e5bb5c36e9077 | trade_date_block_bootstrap | 10146 | BLOCKED | False | True | surrun_7d6a88832441154d6f3529d6 | UNDERPOWERED |
| sspec_b2481e16b39e5bb5c36e9077 | trade_date_block_bootstrap | 10147 | BLOCKED | False | True | surrun_bbbdf2dc09ed20ce5dcea86d | UNDERPOWERED |
| sspec_b2481e16b39e5bb5c36e9077 | trade_date_block_bootstrap | 10148 | BLOCKED | False | True | surrun_3a34047e20211fd7bac3f7d2 | UNDERPOWERED |
| sspec_da7f34f66bcae76f5de31456 | trade_date_block_bootstrap | 10149 | BLOCKED | False | True | surrun_8979b24b7240eceeaddc40dd | UNDERPOWERED |
| sspec_da7f34f66bcae76f5de31456 | trade_date_block_bootstrap | 10150 | BLOCKED | False | True | surrun_6e6dce1702556c9e74357b4f | UNDERPOWERED |
| sspec_da7f34f66bcae76f5de31456 | trade_date_block_bootstrap | 10151 | BLOCKED | False | True | surrun_0622b1c2e034383282ea61a6 | UNDERPOWERED |
| sspec_08b927cfed36292db6022e76 | trade_date_block_bootstrap | 10152 | BLOCKED | False | True | surrun_abe2640e876eecb2b7c70891 | UNDERPOWERED |
| sspec_08b927cfed36292db6022e76 | trade_date_block_bootstrap | 10153 | BLOCKED | False | True | surrun_ddaee432b071b2132bdad8eb | UNDERPOWERED |
| sspec_08b927cfed36292db6022e76 | trade_date_block_bootstrap | 10154 | BLOCKED | False | True | surrun_c108c6c8218018b235d60e87 | UNDERPOWERED |
| sspec_9deffcfe1cd9f8eed3345f3b | trade_date_block_bootstrap | 10155 | BLOCKED | False | True | surrun_e60b8eb0ab39cdfc0a45e0f2 | UNDERPOWERED |
| sspec_9deffcfe1cd9f8eed3345f3b | trade_date_block_bootstrap | 10156 | BLOCKED | False | True | surrun_67b9273fd6c2328d8d204897 | UNDERPOWERED |
| sspec_9deffcfe1cd9f8eed3345f3b | trade_date_block_bootstrap | 10157 | BLOCKED | False | True | surrun_20f2572cd2c8f2226a1ef0c5 | UNDERPOWERED |
| sspec_068dee8a1c12196a48ff6e38 | trade_date_block_bootstrap | 10158 | BLOCKED | False | True | surrun_5a2a69bd9309acc13b53b69f | UNDERPOWERED |
| sspec_068dee8a1c12196a48ff6e38 | trade_date_block_bootstrap | 10159 | BLOCKED | False | True | surrun_1e949401efc961988b37e783 | UNDERPOWERED |
| sspec_068dee8a1c12196a48ff6e38 | trade_date_block_bootstrap | 10160 | BLOCKED | False | True | surrun_10e7854f3b233342daa7eda8 | UNDERPOWERED |
| sspec_22b9a510d85ae10e9a235231 | trade_date_block_bootstrap | 10161 | BLOCKED | False | True | surrun_a9ffc31fedb7db402b214745 | UNDERPOWERED |
| sspec_22b9a510d85ae10e9a235231 | trade_date_block_bootstrap | 10162 | BLOCKED | False | True | surrun_cc9db5e44363e85a5b767a20 | UNDERPOWERED |
| sspec_22b9a510d85ae10e9a235231 | trade_date_block_bootstrap | 10163 | BLOCKED | False | True | surrun_34138213424257023206d736 | UNDERPOWERED |
| sspec_d05c98f1b32052870140910f | trade_date_block_bootstrap | 10164 | BLOCKED | False | True | surrun_b300a71e9cd936e5a57a2ef1 | UNDERPOWERED |
| sspec_d05c98f1b32052870140910f | trade_date_block_bootstrap | 10165 | BLOCKED | False | True | surrun_a8c58eb0c103cd9893eecb9a | UNDERPOWERED |
| sspec_d05c98f1b32052870140910f | trade_date_block_bootstrap | 10166 | BLOCKED | False | True | surrun_cc541cbf3e30459b4adbcd1e | UNDERPOWERED |
| sspec_bb21a754d9c207aab9833762 | trade_date_block_bootstrap | 10167 | BLOCKED | False | True | surrun_1434f886aa22095d0b5426b2 | UNDERPOWERED |
| sspec_bb21a754d9c207aab9833762 | trade_date_block_bootstrap | 10168 | BLOCKED | False | True | surrun_636c700c13440d1c4391bd8e | UNDERPOWERED |
| sspec_bb21a754d9c207aab9833762 | trade_date_block_bootstrap | 10169 | BLOCKED | False | True | surrun_29b4e11d8b2dc514968eb2e2 | UNDERPOWERED |
| sspec_5f831db8c0e9f95a81f6858f | trade_date_block_bootstrap | 10170 | BLOCKED | False | True | surrun_6dbb5deb79ddee2b2a419a9a | UNDERPOWERED |
| sspec_5f831db8c0e9f95a81f6858f | trade_date_block_bootstrap | 10171 | BLOCKED | False | True | surrun_0c93ce22326ab5987556281e | UNDERPOWERED |
| sspec_5f831db8c0e9f95a81f6858f | trade_date_block_bootstrap | 10172 | BLOCKED | False | True | surrun_cd69e6187be7608fdbf9bf3b | UNDERPOWERED |
| sspec_7c721ada57890200ad5316fc | trade_date_block_bootstrap | 10173 | BLOCKED | False | True | surrun_b800882641e49d1f4012c0a5 | UNDERPOWERED |
| sspec_7c721ada57890200ad5316fc | trade_date_block_bootstrap | 10174 | BLOCKED | False | True | surrun_a6c380f40f6742c3c90e2742 | UNDERPOWERED |
| sspec_7c721ada57890200ad5316fc | trade_date_block_bootstrap | 10175 | BLOCKED | False | True | surrun_43fd8f33878e522dcd55356a | UNDERPOWERED |
| sspec_29fc1e53a2fa05d7a46d9100 | trade_date_block_bootstrap | 10176 | BLOCKED | False | True | surrun_6062ad1c4901ccee3fdaf080 | UNDERPOWERED |
| sspec_29fc1e53a2fa05d7a46d9100 | trade_date_block_bootstrap | 10177 | BLOCKED | False | True | surrun_37465f8ac839538b5d1cc4b2 | UNDERPOWERED |
| sspec_29fc1e53a2fa05d7a46d9100 | trade_date_block_bootstrap | 10178 | BLOCKED | False | True | surrun_ab7e7be412af98c56f289634 | UNDERPOWERED |
| sspec_148f1fd71000c07947d55d1a | trade_date_block_bootstrap | 10179 | BLOCKED | False | True | surrun_56a5717a9a78a110bd9d1bc0 | UNDERPOWERED |
| sspec_148f1fd71000c07947d55d1a | trade_date_block_bootstrap | 10180 | BLOCKED | False | True | surrun_ab2c1464fff91afe7c21e56d | UNDERPOWERED |
| sspec_148f1fd71000c07947d55d1a | trade_date_block_bootstrap | 10181 | BLOCKED | False | True | surrun_9ad62b60dcfd4b7c317909c7 | UNDERPOWERED |
| sspec_70c576a78832f1ef384c3d76 | trade_date_block_bootstrap | 10182 | BLOCKED | False | True | surrun_e04d88d8ac32cfdfaa1409a1 | UNDERPOWERED |
| sspec_70c576a78832f1ef384c3d76 | trade_date_block_bootstrap | 10183 | BLOCKED | False | True | surrun_62aba1a76adbfb20ad5323b9 | UNDERPOWERED |
| sspec_70c576a78832f1ef384c3d76 | trade_date_block_bootstrap | 10184 | BLOCKED | False | True | surrun_a09a0266ffbd939246c7e39f | UNDERPOWERED |
| sspec_3d559156c808892bb51553dc | trade_date_block_bootstrap | 10185 | BLOCKED | False | True | surrun_346fed4232876ba966e829b9 | UNDERPOWERED |
| sspec_3d559156c808892bb51553dc | trade_date_block_bootstrap | 10186 | BLOCKED | False | True | surrun_45cd221977dd8914153e8c13 | UNDERPOWERED |
| sspec_3d559156c808892bb51553dc | trade_date_block_bootstrap | 10187 | BLOCKED | False | True | surrun_9341759a7a68591a8e7eb37d | UNDERPOWERED |
| sspec_4b3219b22b82969e17986b28 | trade_date_block_bootstrap | 10188 | BLOCKED | False | True | surrun_f23445a5109fec2c0c4eb739 | UNDERPOWERED |
| sspec_4b3219b22b82969e17986b28 | trade_date_block_bootstrap | 10189 | BLOCKED | False | True | surrun_327e37b80c78b1d9b31856f7 | UNDERPOWERED |
| sspec_4b3219b22b82969e17986b28 | trade_date_block_bootstrap | 10190 | BLOCKED | False | True | surrun_375e48d1f0e5a79d5829d2ca | UNDERPOWERED |
| sspec_831f46078607ce17ef1045ec | trade_date_block_bootstrap | 10191 | BLOCKED | False | True | surrun_2b3720c2f61162d721e2a733 | UNDERPOWERED |
| sspec_831f46078607ce17ef1045ec | trade_date_block_bootstrap | 10192 | BLOCKED | False | True | surrun_1e5c272890fe4ef378d53fd4 | UNDERPOWERED |
| sspec_831f46078607ce17ef1045ec | trade_date_block_bootstrap | 10193 | BLOCKED | False | True | surrun_41d10727f3bd7b535d5f0e80 | UNDERPOWERED |
| sspec_347c0f1c475b1f8e5ea8db95 | trade_date_block_bootstrap | 10194 | BLOCKED | False | True | surrun_7d2459ae32a2044f9748af75 | UNDERPOWERED |
| sspec_347c0f1c475b1f8e5ea8db95 | trade_date_block_bootstrap | 10195 | BLOCKED | False | True | surrun_6c3d6e4cd773b00385c31452 | UNDERPOWERED |
| sspec_347c0f1c475b1f8e5ea8db95 | trade_date_block_bootstrap | 10196 | BLOCKED | False | True | surrun_426f5c44d08e1c06f32466d6 | UNDERPOWERED |
| sspec_7832d85519da01ba5e61c9ad | trade_date_block_bootstrap | 10197 | BLOCKED | False | True | surrun_bcf5d55a6374fc9e2a139333 | UNDERPOWERED |
| sspec_7832d85519da01ba5e61c9ad | trade_date_block_bootstrap | 10198 | BLOCKED | False | True | surrun_7686be8f57bc21b690e03f5c | UNDERPOWERED |
| sspec_7832d85519da01ba5e61c9ad | trade_date_block_bootstrap | 10199 | BLOCKED | False | True | surrun_2460446ade98cb1daf46a3bc | UNDERPOWERED |
| sspec_1828472fa677307f3d940d11 | trade_date_block_bootstrap | 10200 | BLOCKED | False | True | surrun_5a685f369471d28f1a63e8ae | UNDERPOWERED |
| sspec_1828472fa677307f3d940d11 | trade_date_block_bootstrap | 10201 | BLOCKED | False | True | surrun_beb95fd9ef0aef61509dc015 | UNDERPOWERED |
| sspec_1828472fa677307f3d940d11 | trade_date_block_bootstrap | 10202 | BLOCKED | False | True | surrun_ec49675e4bda3db4dbbbd739 | UNDERPOWERED |
| sspec_0fccfd79c440ecddb69bb2dc | trade_date_block_bootstrap | 10203 | BLOCKED | False | True | surrun_712e4541f677811a1249f4e4 | UNDERPOWERED |
| sspec_0fccfd79c440ecddb69bb2dc | trade_date_block_bootstrap | 10204 | BLOCKED | False | True | surrun_1ea59aad13a93cabf387e986 | UNDERPOWERED |
| sspec_0fccfd79c440ecddb69bb2dc | trade_date_block_bootstrap | 10205 | BLOCKED | False | True | surrun_bb527c1414f564734e8e3def | UNDERPOWERED |
| sspec_fd61d11a0368a7fe72cc8ade | trade_date_block_bootstrap | 10206 | BLOCKED | False | True | surrun_c92a336f61920f75644d6103 | UNDERPOWERED |
| sspec_fd61d11a0368a7fe72cc8ade | trade_date_block_bootstrap | 10207 | BLOCKED | False | True | surrun_24437dce4d8e6bc7b95dc75a | UNDERPOWERED |
| sspec_fd61d11a0368a7fe72cc8ade | trade_date_block_bootstrap | 10208 | BLOCKED | False | True | surrun_2d2c27f64fdb77b8ab9a6608 | UNDERPOWERED |
| sspec_dd125675e5b4d7469ee982fc | trade_date_block_bootstrap | 10209 | BLOCKED | False | True | surrun_d56ce686ed022dea1dd0cfd6 | UNDERPOWERED |
| sspec_dd125675e5b4d7469ee982fc | trade_date_block_bootstrap | 10210 | BLOCKED | False | True | surrun_13d9d6a41ce65781aa80b636 | UNDERPOWERED |
| sspec_dd125675e5b4d7469ee982fc | trade_date_block_bootstrap | 10211 | BLOCKED | False | True | surrun_99bee36aec15f75c7985e861 | UNDERPOWERED |
| sspec_9fbb26feebc7dc9e6eb4e31c | trade_date_block_bootstrap | 10212 | BLOCKED | False | True | surrun_87c919935b9e01d5e4e88119 | UNDERPOWERED |
| sspec_9fbb26feebc7dc9e6eb4e31c | trade_date_block_bootstrap | 10213 | BLOCKED | False | True | surrun_851950fa96f9c141ea91c4f7 | UNDERPOWERED |
| sspec_9fbb26feebc7dc9e6eb4e31c | trade_date_block_bootstrap | 10214 | BLOCKED | False | True | surrun_7f46b7764584c047ed290051 | UNDERPOWERED |
| sspec_dce720a6b60901a7d213cd90 | trade_date_block_bootstrap | 10215 | BLOCKED | False | True | surrun_1c0dccf46585003afe2b2b07 | UNDERPOWERED |
| sspec_dce720a6b60901a7d213cd90 | trade_date_block_bootstrap | 10216 | BLOCKED | False | True | surrun_a8607eeede3dbb75f7c83172 | UNDERPOWERED |
| sspec_dce720a6b60901a7d213cd90 | trade_date_block_bootstrap | 10217 | BLOCKED | False | True | surrun_bf2097bcf59555708a44f795 | UNDERPOWERED |
| sspec_7999f013e149e904dc230f2a | trade_date_block_bootstrap | 10218 | BLOCKED | False | True | surrun_8f894c54079120657637ae2a | UNDERPOWERED |
| sspec_7999f013e149e904dc230f2a | trade_date_block_bootstrap | 10219 | BLOCKED | False | True | surrun_945cb66b5c32950925db19e6 | UNDERPOWERED |
| sspec_7999f013e149e904dc230f2a | trade_date_block_bootstrap | 10220 | BLOCKED | False | True | surrun_6b3d2135e070748e1845b3fd | UNDERPOWERED |
| sspec_5b667204dc6b75ecc152f0d1 | trade_date_block_bootstrap | 10221 | BLOCKED | False | True | surrun_fc881a34541a4185225e0851 | UNDERPOWERED |
| sspec_5b667204dc6b75ecc152f0d1 | trade_date_block_bootstrap | 10222 | BLOCKED | False | True | surrun_1c98694ce726bd86705922a6 | UNDERPOWERED |
| sspec_5b667204dc6b75ecc152f0d1 | trade_date_block_bootstrap | 10223 | BLOCKED | False | True | surrun_7dc849171b388000054a9e48 | UNDERPOWERED |
| sspec_e603b3075bc6e35b8cbc3be3 | trade_date_block_bootstrap | 10224 | BLOCKED | False | True | surrun_0da76391c4ed41ab1831b0b3 | UNDERPOWERED |
| sspec_e603b3075bc6e35b8cbc3be3 | trade_date_block_bootstrap | 10225 | BLOCKED | False | True | surrun_3e18d47bd86758a52b9c0830 | UNDERPOWERED |
| sspec_e603b3075bc6e35b8cbc3be3 | trade_date_block_bootstrap | 10226 | BLOCKED | False | True | surrun_cd6d442fe0e1ab093ef5115e | UNDERPOWERED |
| sspec_eef5b1d10312d055b5cf41c8 | trade_date_block_bootstrap | 10227 | BLOCKED | False | True | surrun_77fbe40253a2ba1c858c8c4c | UNDERPOWERED |
| sspec_eef5b1d10312d055b5cf41c8 | trade_date_block_bootstrap | 10228 | BLOCKED | False | True | surrun_dde1ca39df334697ecc8f840 | UNDERPOWERED |
| sspec_eef5b1d10312d055b5cf41c8 | trade_date_block_bootstrap | 10229 | BLOCKED | False | True | surrun_90f99caeb9357a7555139521 | UNDERPOWERED |
| sspec_222ab384a2e47bdefee9ba58 | trade_date_block_bootstrap | 10230 | BLOCKED | False | True | surrun_a9bb414d999032f0ef4c8c60 | UNDERPOWERED |
| sspec_222ab384a2e47bdefee9ba58 | trade_date_block_bootstrap | 10231 | BLOCKED | False | True | surrun_21db1c4658fe53963900e89e | UNDERPOWERED |
| sspec_222ab384a2e47bdefee9ba58 | trade_date_block_bootstrap | 10232 | BLOCKED | False | True | surrun_7fc3cf45ca0467018839c7c5 | UNDERPOWERED |
| sspec_0b99fe38aef1aab26e375a42 | trade_date_block_bootstrap | 10233 | BLOCKED | False | True | surrun_9433ea1c7d8140d6b9e9400e | UNDERPOWERED |
| sspec_0b99fe38aef1aab26e375a42 | trade_date_block_bootstrap | 10234 | BLOCKED | False | True | surrun_f5fa64d17e591b8687ba2226 | UNDERPOWERED |
| sspec_0b99fe38aef1aab26e375a42 | trade_date_block_bootstrap | 10235 | BLOCKED | False | True | surrun_c98d8d8751853009bbb4bd78 | UNDERPOWERED |
| sspec_b2f386d7228951add40f8f58 | trade_date_block_bootstrap | 10236 | BLOCKED | False | True | surrun_d018216e0bb34191cec3b463 | UNDERPOWERED |
| sspec_b2f386d7228951add40f8f58 | trade_date_block_bootstrap | 10237 | BLOCKED | False | True | surrun_1cb5fb5d973ee1e43583e8ff | UNDERPOWERED |
| sspec_b2f386d7228951add40f8f58 | trade_date_block_bootstrap | 10238 | BLOCKED | False | True | surrun_9acfca8d15bb5ead298c9ca1 | UNDERPOWERED |
| sspec_c9347f4c8fecb525ea7bb0cb | trade_date_block_bootstrap | 10239 | BLOCKED | False | True | surrun_cf740eaa49cc6ad14a81a23f | UNDERPOWERED |
| sspec_c9347f4c8fecb525ea7bb0cb | trade_date_block_bootstrap | 10240 | BLOCKED | False | True | surrun_8c0aef72adcb69e8d00e4ce4 | UNDERPOWERED |
| sspec_c9347f4c8fecb525ea7bb0cb | trade_date_block_bootstrap | 10241 | BLOCKED | False | True | surrun_bdd1bfdff1c961a729e0d59c | UNDERPOWERED |
| sspec_8ced88b02c639aad303d9ed6 | trade_date_block_bootstrap | 10242 | BLOCKED | False | True | surrun_faca7b67120d02586c41ffd6 | UNDERPOWERED |
| sspec_8ced88b02c639aad303d9ed6 | trade_date_block_bootstrap | 10243 | BLOCKED | False | True | surrun_2a8b4cf0d8d601b377e6d434 | UNDERPOWERED |
| sspec_8ced88b02c639aad303d9ed6 | trade_date_block_bootstrap | 10244 | BLOCKED | False | True | surrun_3ad4fc2ba4ce09297443239c | UNDERPOWERED |
| sspec_52fd6870c320b613b28db4da | trade_date_block_bootstrap | 10245 | BLOCKED | False | True | surrun_d8a8887d37f352124f78480e | UNDERPOWERED |
| sspec_52fd6870c320b613b28db4da | trade_date_block_bootstrap | 10246 | BLOCKED | False | True | surrun_b6be0cb3ee5ed0802404c466 | UNDERPOWERED |
| sspec_52fd6870c320b613b28db4da | trade_date_block_bootstrap | 10247 | BLOCKED | False | True | surrun_c3c521b23644485d368a6a28 | UNDERPOWERED |
| sspec_4265c4aba76f54d160acdd99 | trade_date_block_bootstrap | 10248 | BLOCKED | False | True | surrun_488eff7f6a8b958b97e0af31 | UNDERPOWERED |
| sspec_4265c4aba76f54d160acdd99 | trade_date_block_bootstrap | 10249 | BLOCKED | False | True | surrun_1474b7a86d7b862a9959a4e2 | UNDERPOWERED |
| sspec_4265c4aba76f54d160acdd99 | trade_date_block_bootstrap | 10250 | BLOCKED | False | True | surrun_31edd8c2b0420d6ba6a9940b | UNDERPOWERED |
| sspec_a891ef6348771ff47ef91f55 | trade_date_block_bootstrap | 10251 | BLOCKED | False | True | surrun_2d2f2d17c2a81f0fc7eb9459 | UNDERPOWERED |
| sspec_a891ef6348771ff47ef91f55 | trade_date_block_bootstrap | 10252 | BLOCKED | False | True | surrun_18fb5c07a890fcc92dbd25e8 | UNDERPOWERED |
| sspec_a891ef6348771ff47ef91f55 | trade_date_block_bootstrap | 10253 | BLOCKED | False | True | surrun_e4ee6d5eb0bc01c303fb9c91 | UNDERPOWERED |
| sspec_38921b819609131f1fedfed3 | trade_date_block_bootstrap | 10254 | BLOCKED | False | True | surrun_70ee358835f66cbddeb0ea27 | UNDERPOWERED |
| sspec_38921b819609131f1fedfed3 | trade_date_block_bootstrap | 10255 | BLOCKED | False | True | surrun_f3d3e21090c69d1439806c8f | UNDERPOWERED |
| sspec_38921b819609131f1fedfed3 | trade_date_block_bootstrap | 10256 | BLOCKED | False | True | surrun_d430bb78ab457955d2d435e0 | UNDERPOWERED |
| sspec_538e4bd64d791e63b37b8211 | trade_date_block_bootstrap | 10257 | BLOCKED | False | True | surrun_47a04ce6a11fe95e175d29cb | UNDERPOWERED |
| sspec_538e4bd64d791e63b37b8211 | trade_date_block_bootstrap | 10258 | BLOCKED | False | True | surrun_3412ca2d723ebba21d3d70ff | UNDERPOWERED |
| sspec_538e4bd64d791e63b37b8211 | trade_date_block_bootstrap | 10259 | BLOCKED | False | True | surrun_0c598d78fdacfa81d69a544d | UNDERPOWERED |
| sspec_bbb01bda4887680914b49dd1 | trade_date_block_bootstrap | 10260 | BLOCKED | False | True | surrun_cb502a9768c3097d27ed369d | UNDERPOWERED |
| sspec_bbb01bda4887680914b49dd1 | trade_date_block_bootstrap | 10261 | BLOCKED | False | True | surrun_979fff2f07fb82d5c641c083 | UNDERPOWERED |
| sspec_bbb01bda4887680914b49dd1 | trade_date_block_bootstrap | 10262 | BLOCKED | False | True | surrun_2ee54e7fe1393984eafc191f | UNDERPOWERED |
| sspec_6207a4edc90a1eda73f9c07a | trade_date_block_bootstrap | 10263 | BLOCKED | False | True | surrun_78b78cfd0a28a0a0cc399a02 | UNDERPOWERED |
| sspec_6207a4edc90a1eda73f9c07a | trade_date_block_bootstrap | 10264 | BLOCKED | False | True | surrun_847b7c0cfe30221a436de86a | UNDERPOWERED |
| sspec_6207a4edc90a1eda73f9c07a | trade_date_block_bootstrap | 10265 | BLOCKED | False | True | surrun_404a32a34f117f25a7422453 | UNDERPOWERED |
| sspec_7bd73bdd58c5b34fc7f858b5 | trade_date_block_bootstrap | 10266 | BLOCKED | False | True | surrun_62bad30b1f8392bcbbf54f6b | UNDERPOWERED |
| sspec_7bd73bdd58c5b34fc7f858b5 | trade_date_block_bootstrap | 10267 | BLOCKED | False | True | surrun_3a6b940ba80f2f6ae675fde2 | UNDERPOWERED |
| sspec_7bd73bdd58c5b34fc7f858b5 | trade_date_block_bootstrap | 10268 | BLOCKED | False | True | surrun_3df5d7d9879a9b24a254e458 | UNDERPOWERED |
| sspec_eba163cfe277594811711a81 | trade_date_block_bootstrap | 10269 | BLOCKED | False | True | surrun_b83230b12a21babed85a531a | UNDERPOWERED |
| sspec_eba163cfe277594811711a81 | trade_date_block_bootstrap | 10270 | BLOCKED | False | True | surrun_a0b737ba4c2ba79f53d07815 | UNDERPOWERED |
| sspec_eba163cfe277594811711a81 | trade_date_block_bootstrap | 10271 | BLOCKED | False | True | surrun_c65fbf45c352520ac0bb7571 | UNDERPOWERED |
| sspec_0af894479cebdd5cc89b6778 | trade_date_block_bootstrap | 10272 | BLOCKED | False | True | surrun_b9e29f37a06dea39087cd646 | UNDERPOWERED |
| sspec_0af894479cebdd5cc89b6778 | trade_date_block_bootstrap | 10273 | BLOCKED | False | True | surrun_73bc5f1831eb1d112b612b8a | UNDERPOWERED |
| sspec_0af894479cebdd5cc89b6778 | trade_date_block_bootstrap | 10274 | BLOCKED | False | True | surrun_0f1b81b5595169ed38101c88 | UNDERPOWERED |
| sspec_ff0452699f84ef333ba84253 | trade_date_block_bootstrap | 10275 | BLOCKED | False | True | surrun_487bf968b5f85214f3b5eadb | UNDERPOWERED |
| sspec_ff0452699f84ef333ba84253 | trade_date_block_bootstrap | 10276 | BLOCKED | False | True | surrun_cfb6dd6876685b3a1b1c0db7 | UNDERPOWERED |
| sspec_ff0452699f84ef333ba84253 | trade_date_block_bootstrap | 10277 | BLOCKED | False | True | surrun_7b479f30424b4da25940255a | UNDERPOWERED |
| sspec_dc1a61174b9ee5cbab27d95c | trade_date_block_bootstrap | 10278 | BLOCKED | False | True | surrun_386719479138f346fbea69e8 | UNDERPOWERED |
| sspec_dc1a61174b9ee5cbab27d95c | trade_date_block_bootstrap | 10279 | BLOCKED | False | True | surrun_b186039f318e6fda34660bd7 | UNDERPOWERED |
| sspec_dc1a61174b9ee5cbab27d95c | trade_date_block_bootstrap | 10280 | BLOCKED | False | True | surrun_ca36b5a34f1f4917aafa9557 | UNDERPOWERED |
| sspec_00550a7fe18875df0c44ce7e | trade_date_block_bootstrap | 10281 | BLOCKED | False | True | surrun_9fcac92242404eea05560df0 | UNDERPOWERED |
| sspec_00550a7fe18875df0c44ce7e | trade_date_block_bootstrap | 10282 | BLOCKED | False | True | surrun_7ef22aa25e692ea9f77ea17b | UNDERPOWERED |
| sspec_00550a7fe18875df0c44ce7e | trade_date_block_bootstrap | 10283 | BLOCKED | False | True | surrun_02dc8fdb97b5a699dc4a048a | UNDERPOWERED |
| sspec_dcb517b41a6f4b47ddda957b | trade_date_block_bootstrap | 10284 | BLOCKED | False | True | surrun_0247641998f8baf8a92160ec | UNDERPOWERED |
| sspec_dcb517b41a6f4b47ddda957b | trade_date_block_bootstrap | 10285 | BLOCKED | False | True | surrun_e24fb921a9904f0d4767f569 | UNDERPOWERED |
| sspec_dcb517b41a6f4b47ddda957b | trade_date_block_bootstrap | 10286 | BLOCKED | False | True | surrun_b3a859e2d3aaf64ede936f27 | UNDERPOWERED |
| sspec_2da0ad738e06829603db55a7 | trade_date_block_bootstrap | 10287 | BLOCKED | False | True | surrun_9d9cbbb892c77ffa8963133b | UNDERPOWERED |
| sspec_2da0ad738e06829603db55a7 | trade_date_block_bootstrap | 10288 | BLOCKED | False | True | surrun_51494260cd7a05c87451ae20 | UNDERPOWERED |
| sspec_2da0ad738e06829603db55a7 | trade_date_block_bootstrap | 10289 | BLOCKED | False | True | surrun_0a0223b1aaa7f5c459534488 | UNDERPOWERED |
| sspec_be4cd0ad733b9eedd964f43b | trade_date_block_bootstrap | 10290 | BLOCKED | False | True | surrun_7a4fd765a1162ffbe06b0736 | UNDERPOWERED |
| sspec_be4cd0ad733b9eedd964f43b | trade_date_block_bootstrap | 10291 | BLOCKED | False | True | surrun_a974950a503386e5a318e353 | UNDERPOWERED |
| sspec_be4cd0ad733b9eedd964f43b | trade_date_block_bootstrap | 10292 | BLOCKED | False | True | surrun_548dfe2c4835a889a74d888b | UNDERPOWERED |
| sspec_2ea8be2fef0c99953be058db | trade_date_block_bootstrap | 10293 | BLOCKED | False | True | surrun_477c4b1fc33533c4bdd88f98 | UNDERPOWERED |
| sspec_2ea8be2fef0c99953be058db | trade_date_block_bootstrap | 10294 | BLOCKED | False | True | surrun_ab5f1b4c2f94bbdeb2aac48f | UNDERPOWERED |
| sspec_2ea8be2fef0c99953be058db | trade_date_block_bootstrap | 10295 | BLOCKED | False | True | surrun_92672d7f33e894bc77776c9c | UNDERPOWERED |
| sspec_adda950f2882047d77c9f571 | trade_date_block_bootstrap | 10296 | BLOCKED | False | True | surrun_834eb7a79a90912ae892a7e5 | UNDERPOWERED |
| sspec_adda950f2882047d77c9f571 | trade_date_block_bootstrap | 10297 | BLOCKED | False | True | surrun_61ad4c150b2b888b8b5d181d | UNDERPOWERED |
| sspec_adda950f2882047d77c9f571 | trade_date_block_bootstrap | 10298 | BLOCKED | False | True | surrun_30883ce2235d7841aabecd47 | UNDERPOWERED |
| sspec_e20c871270f64c22f5ee6f52 | trade_date_block_bootstrap | 10299 | BLOCKED | False | True | surrun_b5c1bfcc13bfeb54d2e4916e | UNDERPOWERED |
| sspec_e20c871270f64c22f5ee6f52 | trade_date_block_bootstrap | 10300 | BLOCKED | False | True | surrun_f8e9b2d40ff98db8bb6ce88d | UNDERPOWERED |
| sspec_e20c871270f64c22f5ee6f52 | trade_date_block_bootstrap | 10301 | BLOCKED | False | True | surrun_710389772ec9c66bb4ba2a68 | UNDERPOWERED |
| sspec_a96d2ce2d4693ffdd1835dd2 | trade_date_block_bootstrap | 10302 | BLOCKED | False | True | surrun_ec09259793aa1ba0cf682fcc | UNDERPOWERED |
| sspec_a96d2ce2d4693ffdd1835dd2 | trade_date_block_bootstrap | 10303 | BLOCKED | False | True | surrun_3a34764db3a024a2288a029a | UNDERPOWERED |
| sspec_a96d2ce2d4693ffdd1835dd2 | trade_date_block_bootstrap | 10304 | BLOCKED | False | True | surrun_a2a159e730403df1de631a7b | UNDERPOWERED |
| sspec_4f15451d74f1c3e4e07cfec7 | trade_date_block_bootstrap | 10305 | BLOCKED | False | True | surrun_e0ea1a40401b807ee3f04ebc | UNDERPOWERED |
| sspec_4f15451d74f1c3e4e07cfec7 | trade_date_block_bootstrap | 10306 | BLOCKED | False | True | surrun_51036f6bb306d1e6178bad83 | UNDERPOWERED |
| sspec_4f15451d74f1c3e4e07cfec7 | trade_date_block_bootstrap | 10307 | BLOCKED | False | True | surrun_cdf6e46a55742933ce276444 | UNDERPOWERED |
| sspec_a128fd7038f27f2e60a4786f | trade_date_block_bootstrap | 10308 | BLOCKED | False | True | surrun_70c2b72b66bfa0fff269d8c5 | UNDERPOWERED |
| sspec_a128fd7038f27f2e60a4786f | trade_date_block_bootstrap | 10309 | BLOCKED | False | True | surrun_3987c02f41a515bef3b2deba | UNDERPOWERED |
| sspec_a128fd7038f27f2e60a4786f | trade_date_block_bootstrap | 10310 | BLOCKED | False | True | surrun_2a3e7bf1e54806ab73bbdfee | UNDERPOWERED |
| sspec_e12267b86e680964aa44200c | trade_date_block_bootstrap | 10311 | BLOCKED | False | True | surrun_b73a09d5d0be2d5653eb3ab4 | UNDERPOWERED |
| sspec_e12267b86e680964aa44200c | trade_date_block_bootstrap | 10312 | BLOCKED | False | True | surrun_b858b71cb7c69d093a1dae7c | UNDERPOWERED |
| sspec_e12267b86e680964aa44200c | trade_date_block_bootstrap | 10313 | BLOCKED | False | True | surrun_2bb70579ef1ed3015d4679bd | UNDERPOWERED |
| sspec_f7f60461859d208503684330 | trade_date_block_bootstrap | 10314 | BLOCKED | False | True | surrun_92e901e088558bcfe41b6473 | UNDERPOWERED |
| sspec_f7f60461859d208503684330 | trade_date_block_bootstrap | 10315 | BLOCKED | False | True | surrun_314ee4acc9a5a0d9e61b1459 | UNDERPOWERED |
| sspec_f7f60461859d208503684330 | trade_date_block_bootstrap | 10316 | BLOCKED | False | True | surrun_2f0080a3a44e68fa5dc0c5d7 | UNDERPOWERED |
| sspec_f17c0941e9d30ed073b12f61 | trade_date_block_bootstrap | 10317 | BLOCKED | False | True | surrun_3883deb396124f26ac109dbe | UNDERPOWERED |
| sspec_f17c0941e9d30ed073b12f61 | trade_date_block_bootstrap | 10318 | BLOCKED | False | True | surrun_c7e716c11928f3fc11df3899 | UNDERPOWERED |
| sspec_f17c0941e9d30ed073b12f61 | trade_date_block_bootstrap | 10319 | BLOCKED | False | True | surrun_cf1f6210ad141a8dc52ecd83 | UNDERPOWERED |

## Machinery Inventory

- `SurrogateStudyRun` schema and deterministic serialization live in `src/alpha_system/governance/surrogate_run.py`.
- `surrogate_flag` is threaded through `TrialLedgerRecord`; true surrogate trials are excluded from production variant/family counts.
- `alpha governance surrogate-calibrate` runs seeded surrogate calibrations in caller-supplied isolated namespaces.
- Real-data calibration over the kill-shot StudySpec remains a coordinator runbook step before FUTSUB-P28 kill-shot resume.
