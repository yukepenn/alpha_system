# Real-Data Surrogate Calibration: sspec_f6cbd88caa0445f0f56d81fd

This coordinator report is value-free: it records ids, run counts, seeds, gate outcomes, and the declared threshold only. It contains no label, feature, return, diagnostic, signal, or cost values.

## Scope

- Declared K per perturbation config: 3
- Bound statement: zero passes in K bounds false-pass rate at about 3/K at 95%.
- Declared primary horizon used for this run: `5m`.
- Perturbation configs: trade_date_block_shuffle, trade_date_block_bootstrap.
- Runtime factor derivation path: `alpha_system.governance.surrogate_run.study_config_for_surrogate_scope` -> `StudyConfig.from_mapping`.
- Declared feature family: `vwap_session_auction`.
- Declared factor count: 6.
- Declared factors: `base_ohlcv_vwap`, `base_ohlcv_anchored_vwap`, `base_ohlcv_distance_to_vwap`, `base_ohlcv_opening_range`, `base_ohlcv_overnight_range`, `base_ohlcv_session_minute`.
- Excluded all-null factor partitions: 0.
- Declared label pack count: 24.
- Declared label versions: `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a`, `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e`, `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64`, `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a`, `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9`, `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022`, `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb`, `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3`, `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b`, `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031`, `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6`, `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2`, `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b`, `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742`, `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57`, `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce`, `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da`, `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515`, `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0`, `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a`, `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b`, `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276`, `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce`, `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b`.
- Staged surrogate sub-config count: 144.
- Off-grid locked label event_ts count: 0.
- Isolated namespace: `/home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_v5_vwap_f6cbd8`.

## Staging Provenance

| Factor | Runtime Factor | Feature Version | Label Version | Feature Partition | Label Partition | Feature Rows | Label Rows | Off-Grid Label event_ts |
|---|---|---|---|---|---|---:|---:|---:|
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_be1ce42491daf2a0213fc8043e2ddf41fa511550fe8df29d6e38887e49483094` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/2097192 | 341120/341120 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_3d828aec4ad0b0fc13a06452042a0221856c34e1bc0b7c3a831b8a9242f2b564` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/2097192 | 341120/341120 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_ff736e80044a17c35a80f5ea9d62bfdcc31c89768df3815972ee96bb6737ee12` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/2097192 | 341120/341120 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_ad24c8083ac314b06e561001bc5bf42306cf54607824a193ab7c97642a5b422a` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/2097192 | 341120/341120 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_c2c3192ee8bbd8bd76c399f6b1dc599c4163576f6b324c19cdb2621f3a2c715d` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/2097192 | 341120/341120 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_70cfe691c9922d8e8141117a93100a42e1367aa1ef238c302618884b6e64b33b` | `lver_4f8fc4387649aba0f6bb997493c0392ed9326567c8e94ba8ab3c24a7aeb4983a` | `ES_2019_full_year` | `ES_2019_fwd_ret_5m` | 349532/2097192 | 341120/341120 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_8016c37da237158b8d88e91b2d5bcfd31230d373715cd8490086cdf6f95d97e8` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/2097648 | 341115/341115 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_1b62114837c0cbd9981f82a868c690da80c679525ef9e7618d78c91ff93a4bf3` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/2097648 | 341115/341115 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_7095d2e279c27251f3920f70a435ad62bda965091687a9ef17b8f5aa5b761c4e` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/2097648 | 341115/341115 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_76e1f424e20d8ef6fb216644574566f8e84f56f8b2b946c3775d5d58c73cc411` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/2097648 | 341115/341115 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_a9d0916dfcf096fb8f78a8553474c1f2e7775742131b995323830d07e89e3645` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/2097648 | 341115/341115 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_dc13579db584037d244bc42f84a6dba766abf6704827e750ac0bbfa821b14b90` | `lver_e58ec699e639e16d4d9309bea1190d4a6bfd0ec1c4636059db8204307ed24e2e` | `ES_2020_full_year` | `ES_2020_fwd_ret_5m` | 349608/2097648 | 341115/341115 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_98740d67c6befed1d5c57664c2ec33d9eb074eaa230b905c2d8fe891c62327f3` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/2120178 | 345881/345881 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_199f65d389466ecf0dafb705671463f60621b00fd26968208f3b5e7a2cd88b7f` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/2120178 | 345881/345881 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_ea14c73d7c73af39d30359d0ac0ae531c132713c0d482c874d945f5caadf996b` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/2120178 | 345881/345881 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_57ec4a4827f2d920c8b24f1ccc8611d0a83d89240b66e30783d0468b25e4ed27` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/2120178 | 345881/345881 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_1a394dd1856d0028100970663d007257f6b0aa73e41e42849a2475d67361492d` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/2120178 | 345881/345881 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_ce3a8c01f17c7c6b1b93a9d58fb44e9543658ccedbe2a09787f1440b91509485` | `lver_151b4d346a2390a33f28246c4602d31d536fd4123dc7297d9ea9c46caed72f64` | `ES_2021_full_year` | `ES_2021_fwd_ret_5m` | 353363/2120178 | 345881/345881 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_bd33b975110a5f19c1af4a110b1a6f9b9424bbb375dff82371f83c9c72d78f09` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/2124714 | 347293/347293 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_13d515a785d5db0539f4aaa7e3e920a7c63e051705c8009365077690c962df11` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/2124714 | 347293/347293 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_3d65b3305f6b6c7caaf1176262f3fd11b36c4a76546edb07e6a293a2050d68a9` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/2124714 | 347293/347293 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_2544067265253611c8bfec9e30ec7b80d9fe0f305387ad423663a63c8b6e7b2c` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/2124714 | 347293/347293 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_90dd9282fb57ed5807ac1d8dac3dbc38a73927cec94053952a21bb9ad14bcb66` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/2124714 | 347293/347293 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_5b3b23ebb76caa216b5dc6ac5f597934b7429700f888e8fa9f950d4e9b3a9a1c` | `lver_1a8a9097ddb8e84d8f9fd76f6f5f4854de61b0874167078127643827bf41c70a` | `ES_2022_full_year` | `ES_2022_fwd_ret_5m` | 354119/2124714 | 347293/347293 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_490fbae9ea7c44359fc005c32fe779eeaabde812221663c1a5d07bc217ca0365` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/2118918 | 346064/346064 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_f53c832b94dc7083fd17919470d7838eb1307098b42198b7e445f1e1f8eea5ce` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/2118918 | 346064/346064 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_0c6ade773ff3a10bf273828f3abbc1cacfcfa92e9a807456b71e05ce94bf9b85` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/2118918 | 346064/346064 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_63666ab2d4a3b0c665a8c8e921f6d1c8304d5050d8ce9f4985de6586b3ad9ae3` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/2118918 | 346064/346064 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_dd9ca1c7ed78c18addaac147b8fdcadcd7b7f0921fe4d8b306ccd9ddeada0156` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/2118918 | 346064/346064 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_02a82a6c8a1af4e39df0cefe0fb3034ca578c3782bdc9a1c53bae7b3d33ef2ae` | `lver_a0f823c60559951296952201f67afa8ea8f1b00802b417538d76f9a8ccd892b9` | `ES_2023_full_year` | `ES_2023_fwd_ret_5m` | 353153/2118918 | 346064/346064 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_f5ba1bbdeb1d879835b59579cb4e2504953434489aa6ef7ed445cdb896bc107d` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/2081148 | 339866/339866 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_d77159b7c3f478a729b23ecd1cdb54bd00301696c53a66cbefdab7047634ea99` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/2081148 | 339866/339866 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_218f7a4d01c3f4fa8d021b6ecd2cd425472f12c4792abe24700f42d55bb4252e` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/2081148 | 339866/339866 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_a92f4590517bb8adfea33a8b6e040f678944a1e7920dc844b1919e407ecd9ea0` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/2081148 | 339866/339866 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_b74239cf2eac020a9f31d1dffe2e09c9fb62187f5e0e533eb8d2edc36166a0a6` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/2081148 | 339866/339866 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_6d84de6c504db7b0b2682cf3deebaf030de39ee3cfccf922f22c62a54ce3689f` | `lver_3eda078c1fc017089c63450a273603f811ca5d5e74c89b976bdbf5177e094022` | `ES_2024_full_year` | `ES_2024_fwd_ret_5m` | 346858/2081148 | 339866/339866 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_16c769a3fbcbf2476ba93fdecfafbbb19a5fd6d01eb93c12ecda653285669608` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/2067366 | 337734/337734 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_8661ab151cdf0bdac18afed2821f5a468d187a6d33fd4e139f128d5fa547aedb` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/2067366 | 337734/337734 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_8caa2e07fd903be5feabc7094acfe2764f1fe44a73f05b7b37c3d3e969f85025` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/2067366 | 337734/337734 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_512626f6a6b5ef2adae2380dbee430ece1894f0b0a462877d013ee268cb74148` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/2067366 | 337734/337734 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_9aad45de8cac1fbf5f2dd20c706534a80fbbe897043c23a6fcbbabdd54328b4f` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/2067366 | 337734/337734 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_f6685498ddfcf1bcb93ee0a7d077db97253d5c1bc3095519b9cfdd6124301bf1` | `lver_e33cc3c199f363a9ce1f7e288c7ed5a590ca3297c3c7c51aa4a2578ea2b51fbb` | `ES_2025_full_year` | `ES_2025_fwd_ret_5m` | 344561/2067366 | 337734/337734 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_ce3cc4095613ec50758924a4dbf4e96037daf1582a1aa868d52972a00d1d3bf0` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/843834 | 138748/138748 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_d918d5684222baea70cd8e23edba2328517b4251fb957d52704a3f1c4003724e` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/843834 | 138748/138748 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_5f20a0b7bd58bf4d58af2b9b080432e68e4b7ea6d1aa1971dedbc527b2e2c558` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/843834 | 138748/138748 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_480353c1b38d70d17875f858d1e763e59137106299e002d767da008cc9dfda70` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/843834 | 138748/138748 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_be6128b58a745787625aa99932f1fe7003254017105ca98f9db8bdbb1ffbc3c5` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/843834 | 138748/138748 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_fe27cadcdba845d110aa154f10256d778760e4971b4ddd41881a1a9ff810a587` | `lver_9fc589d03326280db97e1a703b0b9eaf9477c3ea2ca5ed77ac20c2bca2d496a3` | `ES_2026_full_year` | `ES_2026_fwd_ret_5m` | 140639/843834 | 138748/138748 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_bcbab9040448f4b1e09028a88aaff24f55f362b998916fb44eecd39ba96b4156` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/2099070 | 341715/341715 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_0f9e60b15930d9faffabf95fe0aa0b07689960af256802bb12cb0a43e63693a5` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/2099070 | 341715/341715 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_7164c6485e62bd2074cd101f5deb6d917fcc29ba14386c32b15c2f47568add43` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/2099070 | 341715/341715 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_94ae39cb8ce77532daec87b8da9ae70bd93bc4caf3f7ef09979c809d1f19c9ea` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/2099070 | 341715/341715 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_9ee05dcec72fbb7246babfdbadd1e3c7b30cab5d8556bdd4ff764b0e247c847a` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/2099070 | 341715/341715 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_a3529d2427d3a30b8ee7cbbdb48c4baa3da408b54d45ebb9bf5297a8b2c9cf68` | `lver_bc3706d77d1ecc827edc59776e8c0b54f1ea32c566297592dd39ea0268087c8b` | `NQ_2019_full_year` | `NQ_2019_fwd_ret_5m` | 349845/2099070 | 341715/341715 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_ce2accb70da128de7a6f53c0a48094dd2e90df9798112931516795f97b059139` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/2093574 | 340507/340507 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_ae6273d9e94ea80ce74a5e04000376332bbd0a59226464d0173ee55d6ded4e7a` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/2093574 | 340507/340507 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_0e299e5c4958cfcd27411c4936bf4fd11953cd3ff8293a9145fa6717c43bca8e` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/2093574 | 340507/340507 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_e9760a667d2a5b08355a20ecb789df3f521bee8b6a2356b5a1dcc5f69efcbb3d` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/2093574 | 340507/340507 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_30ba4611cad3354e5467140bf0980d2a5b2996ca6b7426d3aa9dd68409dc7fb0` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/2093574 | 340507/340507 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_cc13dd7ca65d12b87c75ae5baddd5e89b30fba73895498d94711e9cc81b18518` | `lver_026fea7f94f6fd977ad2fa3e60bcc113b9a8a97589237536556d24e118feb031` | `NQ_2020_full_year` | `NQ_2020_fwd_ret_5m` | 348929/2093574 | 340507/340507 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_89ed29d0efbf3009261df4a13e4928c4a1f4334515495ee6a2e5c64566cf348a` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/2120358 | 345938/345938 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_6b136afc59414d09a73c113466a54b480cc3f032d403d7dce71d5ad34634bad9` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/2120358 | 345938/345938 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_8bf09ff5f971c8c05587e7751ee177178cf05c6ccaa04b9a0c2fe62f2607596b` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/2120358 | 345938/345938 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_3b1b2cd52d221cef5d00c2305ca3239c7c2d751dcb97e5132e6aa17509c85e0c` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/2120358 | 345938/345938 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_e3ca7516833c38ef6943ad43989d7f7cae5b32ba45a4b1566b318d29d94ab4ad` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/2120358 | 345938/345938 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_bc1480c710efdc1b61dbb27902b9be8bab003a036c579114e601b1895067e79d` | `lver_f43ffcef350cb5cc75004e9b09b185565dd161798df9727f05c849327034caf6` | `NQ_2021_full_year` | `NQ_2021_fwd_ret_5m` | 353393/2120358 | 345938/345938 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_732eabd764691a7e1d88b753ca24b2356fbca9998956812a8767c3fb609ff71c` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/2124672 | 347280/347280 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_9acda6c7c0cad10ef0b2c33c03478086b00d2aebdacd03498f2fc00f6cc4209e` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/2124672 | 347280/347280 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_797f9374e76f6e0357259007cddd70615af60767b2e8907e6aa6982732a9f665` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/2124672 | 347280/347280 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_245fed770700e67401c453264e5066bf7044cf014aae21d3a1a21c4d593accdd` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/2124672 | 347280/347280 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_bb6f691a09e859b323d7d6d09b7d13657b1329c3f27486ea758d8308a3781c2d` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/2124672 | 347280/347280 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_9c03e309fd2816add7a53bf99a2b5e0fd758a66ff193a2a53e8eb3f37eae02c7` | `lver_3e558a545c10aac327f09ef8b1a5579b150e4a60322120b651678bfa5e7256b2` | `NQ_2022_full_year` | `NQ_2022_fwd_ret_5m` | 354112/2124672 | 347280/347280 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_fa78653e476b4f3a57e1289b2f004506bc26b68f9bb0851a415a6cc0a6fb0ebe` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/2120148 | 346469/346469 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_eb9e8fea9aeda65940c1f96eb90df6bc7aa16fa66abaef468f7da4ba37aa7321` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/2120148 | 346469/346469 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_2579b46addb04a5e9097830c4f946cf2d306f32b4aab1f2b6469dba2f84ccaae` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/2120148 | 346469/346469 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_3df890bdae481b32775d0d6e71dcd53defab2d387f6a1625a8392cb8bcfd152f` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/2120148 | 346469/346469 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_e2341d3186ddd9adc0f9658dd26aacd3b1808bb04918ce13380fcec3b142f39f` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/2120148 | 346469/346469 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_9d9997f342ae598211b5b8e326e2c11aaf37339f64e2f2671cd2f9be721782d2` | `lver_788c5b36ea91d3ee218504edbb634215414ba79950066f4884361c13fe47b99b` | `NQ_2023_full_year` | `NQ_2023_fwd_ret_5m` | 353358/2120148 | 346469/346469 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_6cbfebfef59b9c445c309021f80efece11e25e6668d9f7e2aa3e45123ac0b4d4` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/2081952 | 340126/340126 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_075db18043aebe34adf724494c1788551f69b7971dd71e8437764bf34dcc81ce` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/2081952 | 340126/340126 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_3abb33519dd99882e50b0d4354d659047de9bc52833b03eee6bfd096269b97a4` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/2081952 | 340126/340126 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_c8b0368a258adf8cde9f01b4110084c2392a8a06f5d6fff3b6393f706e81d7b0` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/2081952 | 340126/340126 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_b754bbc8f301a1850644fd4300e990b58fbd5ef8030f9ba29e6a4099346dbf6a` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/2081952 | 340126/340126 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_b02a9cb14d72d4dc073ed2ec68ce2c5970a3259eb8aa0eeffb13924f2b0f0864` | `lver_d55884d1e10337c320e8fe0f59a768b3d2850868b81fd74fb8c9c92fe67d0742` | `NQ_2024_full_year` | `NQ_2024_fwd_ret_5m` | 346992/2081952 | 340126/340126 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_74959eeea52d92651f388ac7f216269bc5111811998f0e7b287081db189648b8` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/2067174 | 337672/337672 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_8ef8670f764fb5f4d97ed2c4f331bfa44b09b85265a20e95d02d1f852889bbfb` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/2067174 | 337672/337672 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_23318b106673be24b6fcb22d028f951ca782d31e6b292c1afb963ddd5125eccb` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/2067174 | 337672/337672 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_bee717702b4f2a7766004ab546f2d51db344cce9808e710c756fb89e7b35efd2` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/2067174 | 337672/337672 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_806d760c92c0282808318cb9abbd48722b2e950d0c70f3cb7b387db4451815e4` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/2067174 | 337672/337672 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_dafbe1ada90b5182aa66e6ac294b332cb84783e26de33aa86d77ee708440048b` | `lver_e44dada099cdaab8716351d737918246c93535ad93e9e686f9c8d1ae21c27c57` | `NQ_2025_full_year` | `NQ_2025_fwd_ret_5m` | 344529/2067174 | 337672/337672 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_31b34963db0a0736c71ab60709e6c087aa81c8adf0282527f074833029184bb5` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/843660 | 138694/138694 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_36cf33a0376f59bde9d8d5c12e7ee31cbe735799c9818f53bf902882ce58a4e3` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/843660 | 138694/138694 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_497d937ac8888dcab8fbfa3d8e2658315edcb4236c160fe6cf0680eff03c50bd` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/843660 | 138694/138694 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_6fbdaaf147043cdaacfe2788701322f8894b80233549178f4b4585ae0227138a` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/843660 | 138694/138694 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_bbe6c7551ebbcdcb6d65ca9de77e7d09d102d41d4fdce431f99035e30fa15819` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/843660 | 138694/138694 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_5951cfbf023bb68039ee17a03381939d132927f1eb9541a222258e4988415bd9` | `lver_0dd4d33df9674717ddcff1f7e1b3d6cde33da721f2bb36b3ad8e22a2e72e6dce` | `NQ_2026_full_year` | `NQ_2026_fwd_ret_5m` | 140610/843660 | 138694/138694 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_efb87396593b65bd4e0adae5c6c35eee260e4b3ac95153a684f361d346c854be` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/1973046 | 305433/305433 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_61032378b5d83c4e0064edfea1d2a77cd8cb1f95644d2a51439dbdb32026c0ec` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/1973046 | 305433/305433 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_ca8dfd832b8e6bcf6187d40b3d461264e8f9fd45f2485c21d2993bd7761e6bf1` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/1973046 | 305433/305433 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_f79a76d047e8a07151494d70420313330a421606d2de1630aefa94029e57840f` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/1973046 | 305433/305433 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_b37a576deeb29b525bbe3b2092ba280e31f42a01f21ddabdb3d8e1ed05894450` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/1973046 | 305433/305433 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_60518bd0feb304264d6d4640e5ed36d63fc3b3743f16a5547cc96ee0a8a21138` | `lver_cde42aaecd43ea9b973fb1b9566dafd4ffd35696efa3f25a0723c3ad616a82da` | `RTY_2019_full_year` | `RTY_2019_fwd_ret_5m` | 328841/1973046 | 305433/305433 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_0be32999d59079c334841f87ed9a7c21259691ca8031234fc069be62d6293990` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/2028510 | 322373/322373 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_f696095a4b60e6ca9a91af41c189d6747d6b61af9f6120172bc374faaad6ed7f` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/2028510 | 322373/322373 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_ad513592467df39b9b02985eeafd925674327cbfab964f1c1d63fe3477afb5bc` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/2028510 | 322373/322373 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_a7eb3c478e3123f5b961c882fd525b1b3004b5bf9576b4099ce7f4458c0dd615` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/2028510 | 322373/322373 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_4c63285b401540663240bf9fd47a236674eaedb98a1d0de0cfb619cbaef3fc7b` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/2028510 | 322373/322373 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_4198e70917536ad09152c79ce825b7b1e360a874de3ab635ab691bcf1e0c75e3` | `lver_75f21845ff10f3e5fc301100a782f93563d078ed468a557dd7925016147a8515` | `RTY_2020_full_year` | `RTY_2020_fwd_ret_5m` | 338085/2028510 | 322373/322373 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_966c9adfdc42f29a33d641ac6ae195a66ce0f2c98222302cdb2cc7346a4e3659` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/2039370 | 322315/322315 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_3e02f481ae4bf68a59ddad95b578e230f81b6f739458d644fdcab7f16ac1ee37` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/2039370 | 322315/322315 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_e30103989c12fbf853e117366872ba624fd6a60a40a4526cd70bec3773cd39ff` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/2039370 | 322315/322315 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_bfd235d6d373a6dbbab252534e3401d9483ca66dd3c8f7f06017d6a7149916e6` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/2039370 | 322315/322315 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_1df68cd24d427651bd1c1768a931c34d8e8e637e3e9b5ba6cbb5a6636b024ddd` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/2039370 | 322315/322315 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_80700999cb432bf6599aca9fbb54f721742c2b850de0eb83ccca9e07a2efd837` | `lver_67b5dd02c7818d913feafdb73b6dfd347e287b510091d3a95699e6916e6ddfe0` | `RTY_2021_full_year` | `RTY_2021_fwd_ret_5m` | 339895/2039370 | 322315/322315 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_8f8da7dffc0e64825cac8fa42a5924baa0e51ccf6d6ea5ecbe881ed870a121c2` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/2070972 | 331308/331308 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_84c037b1b8568972b8e0dba91cd7a25f637d975a9e27e2706668c4e3e56a91c0` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/2070972 | 331308/331308 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_7934921e544565b1f4749351805f287ead9c44188dedebb88e472feb812d2f40` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/2070972 | 331308/331308 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_f6f495589939e38ca8a995b0a3f6a4cd69a7e0aa2ad1e88e2d5c5dc1e9f70fcb` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/2070972 | 331308/331308 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_9ae8636264108f64c0d8ba85b1e5f450d1d4da222870f8cda095959891edeb1d` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/2070972 | 331308/331308 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_f3e1d8af81488b8c241236addc36eac172aa8ef6049e7b3b1306a6aebd2942f1` | `lver_40d478b5c4351a28da47141a7158f69407abb7528f67c13aa99334a3b823665a` | `RTY_2022_full_year` | `RTY_2022_fwd_ret_5m` | 345162/2070972 | 331308/331308 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_e24c30afec71ca4ed4e2f1ca22a762e8251b464fcf57c2b3fa6f08b0f79379c7` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/2054616 | 327109/327109 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_9aff193ea21d844ff82c986491879fc9d78d8414c75ebae0ca0a710565d99d23` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/2054616 | 327109/327109 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_ccc376599781132194762f8756727f8e990691b8902e7b46aeb5253ee86fd838` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/2054616 | 327109/327109 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_1140d8d16730ab2bf068077c4fd38e2bfca2e27401a7298127e4bc45c0871043` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/2054616 | 327109/327109 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_265410fcf40557af3855f1620e7993128b11b391665f09cd737c00b59fe3a8b1` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/2054616 | 327109/327109 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_29bf6618ebb004b4007000c31513e89a49ce875ea804d2efb3341d7c8d6f2c7f` | `lver_5ab0e573cb33cad2ef08f86bf4a19a0e37e9df514855bf720658ce2d2d69933b` | `RTY_2023_full_year` | `RTY_2023_fwd_ret_5m` | 342436/2054616 | 327109/327109 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_05accd010ee4c22db8eb80dbd45ca6e8951795ae016082ce39199e9f34792b43` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/2001240 | 317000/317000 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_c37fabeadc0bcdc5d4ec801f676e09a131c365233bafd1c0130c2f876a41b609` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/2001240 | 317000/317000 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_3aa9e4c9cd69932ef6f452692b29867d7b401b885870bf5f42dac60bfca3eded` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/2001240 | 317000/317000 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_2788967ee64c8a0e8222fdcae10aa2bbcce387aa976aa3d83a9e71a90ca8a5de` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/2001240 | 317000/317000 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_2ca552831f004838e69472a268f84813cf2776e61d9cd204045b61c10c6cc085` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/2001240 | 317000/317000 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_c9e09908d23babdfe8bbff08e51d5988ba367273f252bca6998d2797a7e24b94` | `lver_07924603a1e7ed0e4288803aa93dd63569e14597f35e54a82bcfe0d4117c8276` | `RTY_2024_full_year` | `RTY_2024_fwd_ret_5m` | 333540/2001240 | 317000/317000 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_ad84768c582f455f267b8b4c9000a36ac5f9c5cb6e22bcbb850f830fdcc8de46` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/2001342 | 318544/318544 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_b6bd6d4a5315dd9e9a6a9dc6903e10e37174937246eaaa259b30573753802508` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/2001342 | 318544/318544 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_878b11b1af532920a78cd60f6a6ec6fef6cf55dafb36f4165a52fe936840d810` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/2001342 | 318544/318544 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_9c821f127c3e985ac1523738bf7896ef3209e17d810dac7253c299d3234fa54a` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/2001342 | 318544/318544 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_a2340a7e8e37970ef1dbb1eeb94545f4ef27b282be8c65ea58a55bbc598de8a4` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/2001342 | 318544/318544 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_9cf3eb79eb6849951b9735e3b8fb09127623516271bae00846da420bec8429cd` | `lver_623e0fbb4a453462950fbb3e370820d6cd002e9358b8211c36992601b4112bce` | `RTY_2025_full_year` | `RTY_2025_fwd_ret_5m` | 333557/2001342 | 318544/318544 | 0 |
| `base_ohlcv_vwap` | `base_ohlcv_vwap` | `fver_f9780736489086af1a244584763f9965f725a0b857dfcc54cf19e007dcc338e3` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/831558 | 134990/134990 | 0 |
| `base_ohlcv_anchored_vwap` | `base_ohlcv_anchored_vwap` | `fver_8c10b1dce08dd58b4b82ede636703ef6ff3b3ef7b43b795027d00e8cde3b7795` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/831558 | 134990/134990 | 0 |
| `base_ohlcv_distance_to_vwap` | `base_ohlcv_distance_to_vwap` | `fver_1a8d33c1ec593ff05a741c37a99373a976f14fe1fc2b62fd46e3a26d97734b9b` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/831558 | 134990/134990 | 0 |
| `base_ohlcv_opening_range` | `base_ohlcv_opening_range` | `fver_3d26dbcd5f0c6b489001ede14081552e4dd7677dd620861e73943de5ce15bcef` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/831558 | 134990/134990 | 0 |
| `base_ohlcv_overnight_range` | `base_ohlcv_overnight_range` | `fver_238d5cdda5d1d7c2335419ceaf7deadd3837108268c11885dd82db6aa633d11e` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/831558 | 134990/134990 | 0 |
| `base_ohlcv_session_minute` | `base_ohlcv_session_minute` | `fver_f7bf90b78c898baca58d5bbc559abad41bd06d1582a0c0c88c896809618fa537` | `lver_a33ae299ed3b794fad79f94a0a906ab858f071e4990c834e530061bc1c1a6f2b` | `RTY_2026_full_year` | `RTY_2026_fwd_ret_5m` | 138593/831558 | 134990/134990 | 0 |

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

- Run count: 864
- Error count: 0
- Statistic pass count: 0
- Statistic pass rate: 0.000000
- Eligibility clean count: 720

## Per-Perturbation Counts

| Perturbation | Runs | Errors | Statistic Passes | Eligibility Clean | Statistic Pass Rate | Verdict |
|---|---:|---:|---:|---:|---:|---|
| trade_date_block_bootstrap | 432 | 0 | 0 | 360 | 0.000000 | zero-pass-met |
| trade_date_block_shuffle | 432 | 0 | 0 | 360 | 0.000000 | zero-pass-met |

## Per-Run Seeds And Outcomes

| StudySpec | Perturbation | Seed | Outcome | Statistic Passed | Eligibility Clean | Surrogate ID | Reason |
|---|---|---:|---|---|---|---|---|
| sspec_71e13870ada9f3439366b396 | trade_date_block_shuffle | 9000 | BLOCKED | False | True | surrun_846a2f2a817820e1c28e9c08 | UNDERPOWERED |
| sspec_71e13870ada9f3439366b396 | trade_date_block_shuffle | 9001 | BLOCKED | False | True | surrun_7724fda29df127999862922e | UNDERPOWERED |
| sspec_71e13870ada9f3439366b396 | trade_date_block_shuffle | 9002 | BLOCKED | False | True | surrun_324ca1c7c12b5fe29fbc2abd | UNDERPOWERED |
| sspec_088c0c4cab0bb77b3c0db5cc | trade_date_block_shuffle | 9003 | BLOCKED | False | True | surrun_6f0412f3c286fc04dd792f9b | UNDERPOWERED |
| sspec_088c0c4cab0bb77b3c0db5cc | trade_date_block_shuffle | 9004 | BLOCKED | False | True | surrun_3584cf88753c8cdfb4dfee54 | UNDERPOWERED |
| sspec_088c0c4cab0bb77b3c0db5cc | trade_date_block_shuffle | 9005 | BLOCKED | False | True | surrun_e49a834f98a22cbd5c60b3b1 | UNDERPOWERED |
| sspec_f92099ee740da509337aabd8 | trade_date_block_shuffle | 9006 | BLOCKED | False | True | surrun_42a285965d5e4839097eeeb5 | UNDERPOWERED |
| sspec_f92099ee740da509337aabd8 | trade_date_block_shuffle | 9007 | BLOCKED | False | True | surrun_ff77f38063f141da691057e3 | UNDERPOWERED |
| sspec_f92099ee740da509337aabd8 | trade_date_block_shuffle | 9008 | BLOCKED | False | True | surrun_e3ddf2102ca0a8a8fb126bdd | UNDERPOWERED |
| sspec_f97ad909e3e3bae7cd442eba | trade_date_block_shuffle | 9009 | BLOCKED | False | False | surrun_f1f481ec32fe300d277f4dc2 | UNDERPOWERED |
| sspec_f97ad909e3e3bae7cd442eba | trade_date_block_shuffle | 9010 | BLOCKED | False | False | surrun_0eb6367b0ae8c6b69b5ca31c | UNDERPOWERED |
| sspec_f97ad909e3e3bae7cd442eba | trade_date_block_shuffle | 9011 | BLOCKED | False | False | surrun_9d2e635e8602e717bc1f9288 | UNDERPOWERED |
| sspec_699a13eabc303de9690be6f9 | trade_date_block_shuffle | 9012 | BLOCKED | False | True | surrun_50e42355e349f508c72d7226 | UNDERPOWERED |
| sspec_699a13eabc303de9690be6f9 | trade_date_block_shuffle | 9013 | BLOCKED | False | True | surrun_908b5fca373aaa0ac42c1ca5 | UNDERPOWERED |
| sspec_699a13eabc303de9690be6f9 | trade_date_block_shuffle | 9014 | BLOCKED | False | True | surrun_66e0701bdc62ed185ccb2866 | UNDERPOWERED |
| sspec_9c883e763c74d136d00a4ac9 | trade_date_block_shuffle | 9015 | BLOCKED | False | True | surrun_abdbb17eb43e654371cfcf9d | UNDERPOWERED |
| sspec_9c883e763c74d136d00a4ac9 | trade_date_block_shuffle | 9016 | BLOCKED | False | True | surrun_b1492017dc7b8c5aab124d79 | UNDERPOWERED |
| sspec_9c883e763c74d136d00a4ac9 | trade_date_block_shuffle | 9017 | BLOCKED | False | True | surrun_0cabf44aca64c0c5f7592266 | UNDERPOWERED |
| sspec_537b74c57fb77801308ad239 | trade_date_block_shuffle | 9018 | BLOCKED | False | True | surrun_72528ad78e0c2f662d98c79a | UNDERPOWERED |
| sspec_537b74c57fb77801308ad239 | trade_date_block_shuffle | 9019 | BLOCKED | False | True | surrun_35b335ab88c4b35e8bd4ffe7 | UNDERPOWERED |
| sspec_537b74c57fb77801308ad239 | trade_date_block_shuffle | 9020 | BLOCKED | False | True | surrun_8ddabb014202999cb0b744e2 | UNDERPOWERED |
| sspec_2c7232f7471bfce087ef899c | trade_date_block_shuffle | 9021 | BLOCKED | False | True | surrun_f5d729a364afb9c29445d85b | UNDERPOWERED |
| sspec_2c7232f7471bfce087ef899c | trade_date_block_shuffle | 9022 | BLOCKED | False | True | surrun_54ad38471ee4c1bcc4fb04f7 | UNDERPOWERED |
| sspec_2c7232f7471bfce087ef899c | trade_date_block_shuffle | 9023 | BLOCKED | False | True | surrun_46ce95c1549eb28bd4b669a0 | UNDERPOWERED |
| sspec_dbd173e28cfe2bf0b3b8ebff | trade_date_block_shuffle | 9024 | BLOCKED | False | True | surrun_d5c7bf3593504d3706c89204 | UNDERPOWERED |
| sspec_dbd173e28cfe2bf0b3b8ebff | trade_date_block_shuffle | 9025 | BLOCKED | False | True | surrun_14945d3e6eaf9aae3ec69348 | UNDERPOWERED |
| sspec_dbd173e28cfe2bf0b3b8ebff | trade_date_block_shuffle | 9026 | BLOCKED | False | True | surrun_c43b333aa36ed3caa0a56ca9 | UNDERPOWERED |
| sspec_e7c120acb53f6d56e263fadc | trade_date_block_shuffle | 9027 | BLOCKED | False | False | surrun_8d3d155a946b87c9f83a4c36 | UNDERPOWERED |
| sspec_e7c120acb53f6d56e263fadc | trade_date_block_shuffle | 9028 | BLOCKED | False | False | surrun_1adecc1ccf364d9c8c98bae2 | UNDERPOWERED |
| sspec_e7c120acb53f6d56e263fadc | trade_date_block_shuffle | 9029 | BLOCKED | False | False | surrun_c21288e9c1d6755f2b1e863d | UNDERPOWERED |
| sspec_386403d215c56b35fcc5b52c | trade_date_block_shuffle | 9030 | BLOCKED | False | True | surrun_67c990bbe9d39af2d138aed8 | UNDERPOWERED |
| sspec_386403d215c56b35fcc5b52c | trade_date_block_shuffle | 9031 | BLOCKED | False | True | surrun_cd1414658cf8c3fe92a5a646 | UNDERPOWERED |
| sspec_386403d215c56b35fcc5b52c | trade_date_block_shuffle | 9032 | BLOCKED | False | True | surrun_0bba8b0e274beaf420887ec5 | UNDERPOWERED |
| sspec_4ab842f4b76ad2c0b534c503 | trade_date_block_shuffle | 9033 | BLOCKED | False | True | surrun_cd08e20238105df4e3fcb1ec | UNDERPOWERED |
| sspec_4ab842f4b76ad2c0b534c503 | trade_date_block_shuffle | 9034 | BLOCKED | False | True | surrun_b91f5ca5a049e57c959fb7e3 | UNDERPOWERED |
| sspec_4ab842f4b76ad2c0b534c503 | trade_date_block_shuffle | 9035 | BLOCKED | False | True | surrun_fdb1f04d740e2e204fecc755 | UNDERPOWERED |
| sspec_c11497caee78bbf6f34d27db | trade_date_block_shuffle | 9036 | BLOCKED | False | True | surrun_4ea4ddd67ba12fd1919c8091 | UNDERPOWERED |
| sspec_c11497caee78bbf6f34d27db | trade_date_block_shuffle | 9037 | BLOCKED | False | True | surrun_8dd8abb44f12c4a47fb4ffe2 | UNDERPOWERED |
| sspec_c11497caee78bbf6f34d27db | trade_date_block_shuffle | 9038 | BLOCKED | False | True | surrun_acee95dc3d6765e991e48568 | UNDERPOWERED |
| sspec_7c0b0284f9f795143b75aea9 | trade_date_block_shuffle | 9039 | BLOCKED | False | True | surrun_8e7be4acdd6568a1b1ff08c4 | UNDERPOWERED |
| sspec_7c0b0284f9f795143b75aea9 | trade_date_block_shuffle | 9040 | BLOCKED | False | True | surrun_c20503ac150712ad62ee85f2 | UNDERPOWERED |
| sspec_7c0b0284f9f795143b75aea9 | trade_date_block_shuffle | 9041 | BLOCKED | False | True | surrun_b253f61f1ae1b49868e61fc6 | UNDERPOWERED |
| sspec_b7693add215b26e0043283b6 | trade_date_block_shuffle | 9042 | BLOCKED | False | True | surrun_1eaeb3ab3c03d8c8648a1acb | UNDERPOWERED |
| sspec_b7693add215b26e0043283b6 | trade_date_block_shuffle | 9043 | BLOCKED | False | True | surrun_2620bb135a9d89a9fc118d17 | UNDERPOWERED |
| sspec_b7693add215b26e0043283b6 | trade_date_block_shuffle | 9044 | BLOCKED | False | True | surrun_c942e48731f3f7d2936491dc | UNDERPOWERED |
| sspec_15d04fafd6e3794db2271ebf | trade_date_block_shuffle | 9045 | BLOCKED | False | False | surrun_b3d96eba5f36ad999a4e818d | UNDERPOWERED |
| sspec_15d04fafd6e3794db2271ebf | trade_date_block_shuffle | 9046 | BLOCKED | False | False | surrun_1b6f2fe85f688ef09dbaefe8 | UNDERPOWERED |
| sspec_15d04fafd6e3794db2271ebf | trade_date_block_shuffle | 9047 | BLOCKED | False | False | surrun_8d4641212a23120f22fcd1e5 | UNDERPOWERED |
| sspec_110e51c7aa9eb561134b3190 | trade_date_block_shuffle | 9048 | BLOCKED | False | True | surrun_c64bc81f4bb52b434e96c76e | UNDERPOWERED |
| sspec_110e51c7aa9eb561134b3190 | trade_date_block_shuffle | 9049 | BLOCKED | False | True | surrun_20a7c6e7228bb078ab644e87 | UNDERPOWERED |
| sspec_110e51c7aa9eb561134b3190 | trade_date_block_shuffle | 9050 | BLOCKED | False | True | surrun_659eee95c71d4d25a1b087c7 | UNDERPOWERED |
| sspec_c0c81259945694f00ecf1add | trade_date_block_shuffle | 9051 | BLOCKED | False | True | surrun_6bcc6981ccf954199dc4b790 | UNDERPOWERED |
| sspec_c0c81259945694f00ecf1add | trade_date_block_shuffle | 9052 | BLOCKED | False | True | surrun_e387aa02a1fe0d4abb53bdd2 | UNDERPOWERED |
| sspec_c0c81259945694f00ecf1add | trade_date_block_shuffle | 9053 | BLOCKED | False | True | surrun_fb750c28763ad48a612de385 | UNDERPOWERED |
| sspec_d5c3fdaa393fb21ab395b037 | trade_date_block_shuffle | 9054 | BLOCKED | False | True | surrun_33ca2aa74f451059b4627452 | UNDERPOWERED |
| sspec_d5c3fdaa393fb21ab395b037 | trade_date_block_shuffle | 9055 | BLOCKED | False | True | surrun_aa06d29b094b1e50e4ea5c27 | UNDERPOWERED |
| sspec_d5c3fdaa393fb21ab395b037 | trade_date_block_shuffle | 9056 | BLOCKED | False | True | surrun_2d83b2da44e54731208155c5 | UNDERPOWERED |
| sspec_51984daf0f936e12012b6f9b | trade_date_block_shuffle | 9057 | BLOCKED | False | True | surrun_e81631ef77f339a18f516ba2 | UNDERPOWERED |
| sspec_51984daf0f936e12012b6f9b | trade_date_block_shuffle | 9058 | BLOCKED | False | True | surrun_d222189c4a8f3b267b1da3de | UNDERPOWERED |
| sspec_51984daf0f936e12012b6f9b | trade_date_block_shuffle | 9059 | BLOCKED | False | True | surrun_03b0703cd82aa8e03f50e0fc | UNDERPOWERED |
| sspec_2c38a886b417233d0f329de4 | trade_date_block_shuffle | 9060 | BLOCKED | False | True | surrun_e4fab6b651bbe2f9f5545059 | UNDERPOWERED |
| sspec_2c38a886b417233d0f329de4 | trade_date_block_shuffle | 9061 | BLOCKED | False | True | surrun_2884c3e78fefaef1e055339a | UNDERPOWERED |
| sspec_2c38a886b417233d0f329de4 | trade_date_block_shuffle | 9062 | BLOCKED | False | True | surrun_9fbbb2749b1206ae90ea5677 | UNDERPOWERED |
| sspec_673a4ecda99f38d9afc2407d | trade_date_block_shuffle | 9063 | BLOCKED | False | False | surrun_eeea4c3f47a3536ff7d299d4 | UNDERPOWERED |
| sspec_673a4ecda99f38d9afc2407d | trade_date_block_shuffle | 9064 | BLOCKED | False | False | surrun_0ac25be7aeaae24f242f2ba4 | UNDERPOWERED |
| sspec_673a4ecda99f38d9afc2407d | trade_date_block_shuffle | 9065 | BLOCKED | False | False | surrun_d29e0f068ecada40e2df71b1 | UNDERPOWERED |
| sspec_9d3f841efb7e37a1b2f6a4ea | trade_date_block_shuffle | 9066 | BLOCKED | False | True | surrun_d087a0167e5c9ec84550deb4 | UNDERPOWERED |
| sspec_9d3f841efb7e37a1b2f6a4ea | trade_date_block_shuffle | 9067 | BLOCKED | False | True | surrun_48b8086b998db8207c10cd47 | UNDERPOWERED |
| sspec_9d3f841efb7e37a1b2f6a4ea | trade_date_block_shuffle | 9068 | BLOCKED | False | True | surrun_ebead71b0e13fe4eca2686b8 | UNDERPOWERED |
| sspec_85528ce6713165fc56411d18 | trade_date_block_shuffle | 9069 | BLOCKED | False | True | surrun_7ccb49ceba17ed8fb3a88a84 | UNDERPOWERED |
| sspec_85528ce6713165fc56411d18 | trade_date_block_shuffle | 9070 | BLOCKED | False | True | surrun_1afa4ce9a8962f42ad703429 | UNDERPOWERED |
| sspec_85528ce6713165fc56411d18 | trade_date_block_shuffle | 9071 | BLOCKED | False | True | surrun_1fbe8ab770f7fa7010c5c81d | UNDERPOWERED |
| sspec_612a22a1e3fae57e3fe9be6e | trade_date_block_shuffle | 9072 | BLOCKED | False | True | surrun_1d586ad37a986fbf330bf660 | UNDERPOWERED |
| sspec_612a22a1e3fae57e3fe9be6e | trade_date_block_shuffle | 9073 | BLOCKED | False | True | surrun_c95ea5d15ec2add582dd1eec | UNDERPOWERED |
| sspec_612a22a1e3fae57e3fe9be6e | trade_date_block_shuffle | 9074 | BLOCKED | False | True | surrun_393f5d8ea101b8004ba63efb | UNDERPOWERED |
| sspec_cf7ac520fcc429b6475439e4 | trade_date_block_shuffle | 9075 | BLOCKED | False | True | surrun_ed2271a2b5e634cf46ab4fef | UNDERPOWERED |
| sspec_cf7ac520fcc429b6475439e4 | trade_date_block_shuffle | 9076 | BLOCKED | False | True | surrun_a583991f4f9dba2c664c55f4 | UNDERPOWERED |
| sspec_cf7ac520fcc429b6475439e4 | trade_date_block_shuffle | 9077 | BLOCKED | False | True | surrun_d04c82b16aa08f30c6b34c45 | UNDERPOWERED |
| sspec_49147e59ea35c1524af9e45f | trade_date_block_shuffle | 9078 | BLOCKED | False | True | surrun_91b011a07dc43990fa124b5b | UNDERPOWERED |
| sspec_49147e59ea35c1524af9e45f | trade_date_block_shuffle | 9079 | BLOCKED | False | True | surrun_6ac15c29249998a014a4b906 | UNDERPOWERED |
| sspec_49147e59ea35c1524af9e45f | trade_date_block_shuffle | 9080 | BLOCKED | False | True | surrun_849dcf70c731f231acc71295 | UNDERPOWERED |
| sspec_7046ae570b393874b90a86dc | trade_date_block_shuffle | 9081 | BLOCKED | False | False | surrun_08f20618751bd5c9f20d54dc | UNDERPOWERED |
| sspec_7046ae570b393874b90a86dc | trade_date_block_shuffle | 9082 | BLOCKED | False | False | surrun_310eb4ef7d9ec472d62d8d26 | UNDERPOWERED |
| sspec_7046ae570b393874b90a86dc | trade_date_block_shuffle | 9083 | BLOCKED | False | False | surrun_4fc03335c685a8ab7839053a | UNDERPOWERED |
| sspec_45e43b7e26bff0f649022dbe | trade_date_block_shuffle | 9084 | BLOCKED | False | True | surrun_409e45f52367366d619bb75e | UNDERPOWERED |
| sspec_45e43b7e26bff0f649022dbe | trade_date_block_shuffle | 9085 | BLOCKED | False | True | surrun_96ed91cc30e1a32770274754 | UNDERPOWERED |
| sspec_45e43b7e26bff0f649022dbe | trade_date_block_shuffle | 9086 | BLOCKED | False | True | surrun_4f406c027a9e0b683fde44d4 | UNDERPOWERED |
| sspec_1667ddb835e6855009b531b3 | trade_date_block_shuffle | 9087 | BLOCKED | False | True | surrun_bb0859a6c30eb9491819f60d | UNDERPOWERED |
| sspec_1667ddb835e6855009b531b3 | trade_date_block_shuffle | 9088 | BLOCKED | False | True | surrun_02bf6fc415cf7c239bdc5ee2 | UNDERPOWERED |
| sspec_1667ddb835e6855009b531b3 | trade_date_block_shuffle | 9089 | BLOCKED | False | True | surrun_66faccd18ce588a3b2799a45 | UNDERPOWERED |
| sspec_7ae5f694ea2dae90ef35070a | trade_date_block_shuffle | 9090 | BLOCKED | False | True | surrun_ed6a78dc75c2e6164916ad5f | UNDERPOWERED |
| sspec_7ae5f694ea2dae90ef35070a | trade_date_block_shuffle | 9091 | BLOCKED | False | True | surrun_6f25b816ecb56335fc73e06d | UNDERPOWERED |
| sspec_7ae5f694ea2dae90ef35070a | trade_date_block_shuffle | 9092 | BLOCKED | False | True | surrun_dc6e886dc07389d2e23f2a69 | UNDERPOWERED |
| sspec_5a1389ac8c1ce500c91adca0 | trade_date_block_shuffle | 9093 | BLOCKED | False | True | surrun_b7f23c3a95432c1f75710f66 | UNDERPOWERED |
| sspec_5a1389ac8c1ce500c91adca0 | trade_date_block_shuffle | 9094 | BLOCKED | False | True | surrun_0e91a05dcce4e360c005be09 | UNDERPOWERED |
| sspec_5a1389ac8c1ce500c91adca0 | trade_date_block_shuffle | 9095 | BLOCKED | False | True | surrun_37aaf774ee5f3556b7949ce3 | UNDERPOWERED |
| sspec_65e6f5137f49203e67039618 | trade_date_block_shuffle | 9096 | BLOCKED | False | True | surrun_f1e966a5b258ea2fa1d764f5 | UNDERPOWERED |
| sspec_65e6f5137f49203e67039618 | trade_date_block_shuffle | 9097 | BLOCKED | False | True | surrun_f63da389f54ffb6ffdf4be9a | UNDERPOWERED |
| sspec_65e6f5137f49203e67039618 | trade_date_block_shuffle | 9098 | BLOCKED | False | True | surrun_e05d7bb168141fbc631a4aa3 | UNDERPOWERED |
| sspec_f0a44f35c13e75f6968eac4e | trade_date_block_shuffle | 9099 | BLOCKED | False | False | surrun_356c8e95f278dbe8e6e52d66 | UNDERPOWERED |
| sspec_f0a44f35c13e75f6968eac4e | trade_date_block_shuffle | 9100 | BLOCKED | False | False | surrun_bfc5f302eed6a41ce71a190b | UNDERPOWERED |
| sspec_f0a44f35c13e75f6968eac4e | trade_date_block_shuffle | 9101 | BLOCKED | False | False | surrun_4b9dc3a2d7288099dd97d869 | UNDERPOWERED |
| sspec_3845e486992283683dce9ba3 | trade_date_block_shuffle | 9102 | BLOCKED | False | True | surrun_eb260649036c8ec44e320885 | UNDERPOWERED |
| sspec_3845e486992283683dce9ba3 | trade_date_block_shuffle | 9103 | BLOCKED | False | True | surrun_e6df0d1f66f470a1a865bbfb | UNDERPOWERED |
| sspec_3845e486992283683dce9ba3 | trade_date_block_shuffle | 9104 | BLOCKED | False | True | surrun_27f4633cfb8be3fe525e2405 | UNDERPOWERED |
| sspec_3a8306dcf1c29dd56009b781 | trade_date_block_shuffle | 9105 | BLOCKED | False | True | surrun_117bfa6211ee4a31bf16163a | UNDERPOWERED |
| sspec_3a8306dcf1c29dd56009b781 | trade_date_block_shuffle | 9106 | BLOCKED | False | True | surrun_116031fed4a7e659efbfad6b | UNDERPOWERED |
| sspec_3a8306dcf1c29dd56009b781 | trade_date_block_shuffle | 9107 | BLOCKED | False | True | surrun_93de4fa008a322b09c456be6 | UNDERPOWERED |
| sspec_2263d90cd6e363a844b4a8a5 | trade_date_block_shuffle | 9108 | BLOCKED | False | True | surrun_275d0f039714bbbec7e7899f | UNDERPOWERED |
| sspec_2263d90cd6e363a844b4a8a5 | trade_date_block_shuffle | 9109 | BLOCKED | False | True | surrun_4f8b5d35574042c5f9995bb6 | UNDERPOWERED |
| sspec_2263d90cd6e363a844b4a8a5 | trade_date_block_shuffle | 9110 | BLOCKED | False | True | surrun_d891951f485b41f7e3566bce | UNDERPOWERED |
| sspec_25dbac39b219301bab1a5177 | trade_date_block_shuffle | 9111 | BLOCKED | False | True | surrun_5afd8ed624dc326d56989334 | UNDERPOWERED |
| sspec_25dbac39b219301bab1a5177 | trade_date_block_shuffle | 9112 | BLOCKED | False | True | surrun_d48366182810bf36a449fda4 | UNDERPOWERED |
| sspec_25dbac39b219301bab1a5177 | trade_date_block_shuffle | 9113 | BLOCKED | False | True | surrun_69023086c414e8f709fb2585 | UNDERPOWERED |
| sspec_f205ae668f64e67184d42145 | trade_date_block_shuffle | 9114 | BLOCKED | False | True | surrun_ee3a659b0f17f9fd0caecbf1 | UNDERPOWERED |
| sspec_f205ae668f64e67184d42145 | trade_date_block_shuffle | 9115 | BLOCKED | False | True | surrun_7189317fee3854a1343fa1ec | UNDERPOWERED |
| sspec_f205ae668f64e67184d42145 | trade_date_block_shuffle | 9116 | BLOCKED | False | True | surrun_3d136f25ed5285fb4412d5d9 | UNDERPOWERED |
| sspec_29b931a0f343003bbd02d01c | trade_date_block_shuffle | 9117 | BLOCKED | False | False | surrun_5a707847bdb42e1650452212 | UNDERPOWERED |
| sspec_29b931a0f343003bbd02d01c | trade_date_block_shuffle | 9118 | BLOCKED | False | False | surrun_daf589aa3a3b4fc497c10f0e | UNDERPOWERED |
| sspec_29b931a0f343003bbd02d01c | trade_date_block_shuffle | 9119 | BLOCKED | False | False | surrun_7c3ae7f186b274ee6505fe20 | UNDERPOWERED |
| sspec_862924c23856461f929ae080 | trade_date_block_shuffle | 9120 | BLOCKED | False | True | surrun_9b1077f90e2c8c80d329ae81 | UNDERPOWERED |
| sspec_862924c23856461f929ae080 | trade_date_block_shuffle | 9121 | BLOCKED | False | True | surrun_a09a61d30c662d679c3caa63 | UNDERPOWERED |
| sspec_862924c23856461f929ae080 | trade_date_block_shuffle | 9122 | BLOCKED | False | True | surrun_dfa24b6f4c9812a331c1ec86 | UNDERPOWERED |
| sspec_bc3d1222efb35bfe10f89929 | trade_date_block_shuffle | 9123 | BLOCKED | False | True | surrun_3a9b845d5dc1936b91cbba7a | UNDERPOWERED |
| sspec_bc3d1222efb35bfe10f89929 | trade_date_block_shuffle | 9124 | BLOCKED | False | True | surrun_b99bdfe89080527943addda8 | UNDERPOWERED |
| sspec_bc3d1222efb35bfe10f89929 | trade_date_block_shuffle | 9125 | BLOCKED | False | True | surrun_34c48d71e8ae2dbed24cb2e8 | UNDERPOWERED |
| sspec_b7c870f978b38bf3f62a7624 | trade_date_block_shuffle | 9126 | BLOCKED | False | True | surrun_06790672129eed9454fa5e25 | UNDERPOWERED |
| sspec_b7c870f978b38bf3f62a7624 | trade_date_block_shuffle | 9127 | BLOCKED | False | True | surrun_c3a9225b8f1464f8f3394cab | UNDERPOWERED |
| sspec_b7c870f978b38bf3f62a7624 | trade_date_block_shuffle | 9128 | BLOCKED | False | True | surrun_c4a69a751b729f96bb6ded69 | UNDERPOWERED |
| sspec_a4d225065125a873eb137d03 | trade_date_block_shuffle | 9129 | BLOCKED | False | True | surrun_51ae2acc3374ad7b10944c51 | UNDERPOWERED |
| sspec_a4d225065125a873eb137d03 | trade_date_block_shuffle | 9130 | BLOCKED | False | True | surrun_b4ff4b606abf3c7c0f5496a1 | UNDERPOWERED |
| sspec_a4d225065125a873eb137d03 | trade_date_block_shuffle | 9131 | BLOCKED | False | True | surrun_2b823a8cc1d50deb04b04dee | UNDERPOWERED |
| sspec_1e25e9de8dba2b24f0e64c47 | trade_date_block_shuffle | 9132 | BLOCKED | False | True | surrun_411762fe5c67c673d6e20b3e | UNDERPOWERED |
| sspec_1e25e9de8dba2b24f0e64c47 | trade_date_block_shuffle | 9133 | BLOCKED | False | True | surrun_470bc6f7f937990cc068e63c | UNDERPOWERED |
| sspec_1e25e9de8dba2b24f0e64c47 | trade_date_block_shuffle | 9134 | BLOCKED | False | True | surrun_2da9b3f1f3377ac13603aca3 | UNDERPOWERED |
| sspec_71a3aa976b4c193d945945ab | trade_date_block_shuffle | 9135 | BLOCKED | False | False | surrun_e2d4c6e0a31a8e66fc56437e | UNDERPOWERED |
| sspec_71a3aa976b4c193d945945ab | trade_date_block_shuffle | 9136 | BLOCKED | False | False | surrun_0cabf220ae71df741b9ed96c | UNDERPOWERED |
| sspec_71a3aa976b4c193d945945ab | trade_date_block_shuffle | 9137 | BLOCKED | False | False | surrun_2070954f46b6f9dca86db120 | UNDERPOWERED |
| sspec_7d5dad24d016cd9913744df7 | trade_date_block_shuffle | 9138 | BLOCKED | False | True | surrun_7ade9bc4487856fcec771be2 | UNDERPOWERED |
| sspec_7d5dad24d016cd9913744df7 | trade_date_block_shuffle | 9139 | BLOCKED | False | True | surrun_3004ae2ac65ebcf8de68a358 | UNDERPOWERED |
| sspec_7d5dad24d016cd9913744df7 | trade_date_block_shuffle | 9140 | BLOCKED | False | True | surrun_1ebbfb020a18353027244992 | UNDERPOWERED |
| sspec_04e96bf03de43a8dc0759971 | trade_date_block_shuffle | 9141 | BLOCKED | False | True | surrun_d592f4c9a387c6e19cbfd155 | UNDERPOWERED |
| sspec_04e96bf03de43a8dc0759971 | trade_date_block_shuffle | 9142 | BLOCKED | False | True | surrun_41ba788c1024f59dab4669be | UNDERPOWERED |
| sspec_04e96bf03de43a8dc0759971 | trade_date_block_shuffle | 9143 | BLOCKED | False | True | surrun_8dd964a89fb0552db2a817b2 | UNDERPOWERED |
| sspec_a227d866d2a460e84f4836d4 | trade_date_block_shuffle | 9144 | BLOCKED | False | True | surrun_2a33c9329adc94fb36cdd123 | UNDERPOWERED |
| sspec_a227d866d2a460e84f4836d4 | trade_date_block_shuffle | 9145 | BLOCKED | False | True | surrun_a0957c89e13acb48e6fa7b32 | UNDERPOWERED |
| sspec_a227d866d2a460e84f4836d4 | trade_date_block_shuffle | 9146 | BLOCKED | False | True | surrun_051b23ee3bbe26d091cb47fc | UNDERPOWERED |
| sspec_d9bf8c128f48a5aa14489b6a | trade_date_block_shuffle | 9147 | BLOCKED | False | True | surrun_86b530c7f7c060cda44fd6e4 | UNDERPOWERED |
| sspec_d9bf8c128f48a5aa14489b6a | trade_date_block_shuffle | 9148 | BLOCKED | False | True | surrun_99ee491123ce4f849728675b | UNDERPOWERED |
| sspec_d9bf8c128f48a5aa14489b6a | trade_date_block_shuffle | 9149 | BLOCKED | False | True | surrun_86a3c79000f93e32e2e51496 | UNDERPOWERED |
| sspec_ce04f0a862ee4837d5976f28 | trade_date_block_shuffle | 9150 | BLOCKED | False | True | surrun_14914e161ca633e29149ccb7 | UNDERPOWERED |
| sspec_ce04f0a862ee4837d5976f28 | trade_date_block_shuffle | 9151 | BLOCKED | False | True | surrun_5e77765f020cc53a31451085 | UNDERPOWERED |
| sspec_ce04f0a862ee4837d5976f28 | trade_date_block_shuffle | 9152 | BLOCKED | False | True | surrun_a04ef2a9509b94df37d215af | UNDERPOWERED |
| sspec_3163751e574ca37179d3396a | trade_date_block_shuffle | 9153 | BLOCKED | False | False | surrun_24bf9230798125aae59cf426 | UNDERPOWERED |
| sspec_3163751e574ca37179d3396a | trade_date_block_shuffle | 9154 | BLOCKED | False | False | surrun_d296ba21f100a2abb0f08863 | UNDERPOWERED |
| sspec_3163751e574ca37179d3396a | trade_date_block_shuffle | 9155 | BLOCKED | False | False | surrun_7fc8cf069bd434156a77a1b5 | UNDERPOWERED |
| sspec_e4408d6ef919c21990034bd0 | trade_date_block_shuffle | 9156 | BLOCKED | False | True | surrun_54a10b382c58fd75920eac1e | UNDERPOWERED |
| sspec_e4408d6ef919c21990034bd0 | trade_date_block_shuffle | 9157 | BLOCKED | False | True | surrun_2dd681ae74a0d1acce9aa59d | UNDERPOWERED |
| sspec_e4408d6ef919c21990034bd0 | trade_date_block_shuffle | 9158 | BLOCKED | False | True | surrun_937ff753297a8b5489baceda | UNDERPOWERED |
| sspec_682011f6aa35bc534d66ae33 | trade_date_block_shuffle | 9159 | BLOCKED | False | True | surrun_1f8fae3fa9542a35a6e9bf8b | UNDERPOWERED |
| sspec_682011f6aa35bc534d66ae33 | trade_date_block_shuffle | 9160 | BLOCKED | False | True | surrun_9e069c4b496b874e885e5e5c | UNDERPOWERED |
| sspec_682011f6aa35bc534d66ae33 | trade_date_block_shuffle | 9161 | BLOCKED | False | True | surrun_64da33a59728d21c1364f95c | UNDERPOWERED |
| sspec_44a8c2364695282be9865b23 | trade_date_block_shuffle | 9162 | BLOCKED | False | True | surrun_8326af414365c565f502e2d2 | UNDERPOWERED |
| sspec_44a8c2364695282be9865b23 | trade_date_block_shuffle | 9163 | BLOCKED | False | True | surrun_b4d970ee10fe9bd6db9d6c6d | UNDERPOWERED |
| sspec_44a8c2364695282be9865b23 | trade_date_block_shuffle | 9164 | BLOCKED | False | True | surrun_192920ffce1b534b8aced9df | UNDERPOWERED |
| sspec_5ff3e9f63b2f32c443d11929 | trade_date_block_shuffle | 9165 | BLOCKED | False | True | surrun_d0a7bbbf00fbe10febd00b74 | UNDERPOWERED |
| sspec_5ff3e9f63b2f32c443d11929 | trade_date_block_shuffle | 9166 | BLOCKED | False | True | surrun_7ada6b1b31671aa369c49c0b | UNDERPOWERED |
| sspec_5ff3e9f63b2f32c443d11929 | trade_date_block_shuffle | 9167 | BLOCKED | False | True | surrun_271fda747a158bf7454d22bf | UNDERPOWERED |
| sspec_a0213fc1cf2176738be0b134 | trade_date_block_shuffle | 9168 | BLOCKED | False | True | surrun_473dee4b1fbe12037a8bcf01 | UNDERPOWERED |
| sspec_a0213fc1cf2176738be0b134 | trade_date_block_shuffle | 9169 | BLOCKED | False | True | surrun_672c2babb63545606efacd3d | UNDERPOWERED |
| sspec_a0213fc1cf2176738be0b134 | trade_date_block_shuffle | 9170 | BLOCKED | False | True | surrun_b6a6d18557bb2fc81877ba2c | UNDERPOWERED |
| sspec_297d60252087f608b59ccb3a | trade_date_block_shuffle | 9171 | BLOCKED | False | False | surrun_e4956a87283835c253608650 | UNDERPOWERED |
| sspec_297d60252087f608b59ccb3a | trade_date_block_shuffle | 9172 | BLOCKED | False | False | surrun_216d448edd1f309afe75e6a4 | UNDERPOWERED |
| sspec_297d60252087f608b59ccb3a | trade_date_block_shuffle | 9173 | BLOCKED | False | False | surrun_c45171687208ee3c39f1b44c | UNDERPOWERED |
| sspec_677919c47329048120d6a0a1 | trade_date_block_shuffle | 9174 | BLOCKED | False | True | surrun_62f493207ba4915a0c9764b2 | UNDERPOWERED |
| sspec_677919c47329048120d6a0a1 | trade_date_block_shuffle | 9175 | BLOCKED | False | True | surrun_b486453f7adeebb889e45480 | UNDERPOWERED |
| sspec_677919c47329048120d6a0a1 | trade_date_block_shuffle | 9176 | BLOCKED | False | True | surrun_f7bb56f1a50f642a414bbae5 | UNDERPOWERED |
| sspec_c9bd816912f5d0e3062596fd | trade_date_block_shuffle | 9177 | BLOCKED | False | True | surrun_03c68f852f8697a7bdf900c5 | UNDERPOWERED |
| sspec_c9bd816912f5d0e3062596fd | trade_date_block_shuffle | 9178 | BLOCKED | False | True | surrun_f9a3b49e1efdb4074d46a59e | UNDERPOWERED |
| sspec_c9bd816912f5d0e3062596fd | trade_date_block_shuffle | 9179 | BLOCKED | False | True | surrun_43ff620ee9a53a9e9151b098 | UNDERPOWERED |
| sspec_96b5c59ca85ab728516f3685 | trade_date_block_shuffle | 9180 | BLOCKED | False | True | surrun_5a0e127a9d3a0d454b108da3 | UNDERPOWERED |
| sspec_96b5c59ca85ab728516f3685 | trade_date_block_shuffle | 9181 | BLOCKED | False | True | surrun_b23225dd4e4a9e8f01ca2fa9 | UNDERPOWERED |
| sspec_96b5c59ca85ab728516f3685 | trade_date_block_shuffle | 9182 | BLOCKED | False | True | surrun_8b89b3ccec6f1e2e63407168 | UNDERPOWERED |
| sspec_c53ce1c1bab5dbceded68cca | trade_date_block_shuffle | 9183 | BLOCKED | False | True | surrun_5925b6ae6cae11e431a6a29f | UNDERPOWERED |
| sspec_c53ce1c1bab5dbceded68cca | trade_date_block_shuffle | 9184 | BLOCKED | False | True | surrun_8d15a1c78f9155764ec5ef4e | UNDERPOWERED |
| sspec_c53ce1c1bab5dbceded68cca | trade_date_block_shuffle | 9185 | BLOCKED | False | True | surrun_9438fc303d74f6562319610d | UNDERPOWERED |
| sspec_f7fceba9afe46c9f31c564cc | trade_date_block_shuffle | 9186 | BLOCKED | False | True | surrun_0b7468ff80d86846952aca1b | UNDERPOWERED |
| sspec_f7fceba9afe46c9f31c564cc | trade_date_block_shuffle | 9187 | BLOCKED | False | True | surrun_8cb9935863ec2c9f1d391003 | UNDERPOWERED |
| sspec_f7fceba9afe46c9f31c564cc | trade_date_block_shuffle | 9188 | BLOCKED | False | True | surrun_9487f3f5eb4ebaf0205939c4 | UNDERPOWERED |
| sspec_db044241ed2a1c38f7be6890 | trade_date_block_shuffle | 9189 | BLOCKED | False | False | surrun_622c585312de9616cc7dfb8e | UNDERPOWERED |
| sspec_db044241ed2a1c38f7be6890 | trade_date_block_shuffle | 9190 | BLOCKED | False | False | surrun_fd59420a5098c4ffcd9ed531 | UNDERPOWERED |
| sspec_db044241ed2a1c38f7be6890 | trade_date_block_shuffle | 9191 | BLOCKED | False | False | surrun_94605d32ca7a6b65a5b38e3f | UNDERPOWERED |
| sspec_1df124b26123342e8fb546f5 | trade_date_block_shuffle | 9192 | BLOCKED | False | True | surrun_31518fc4c64ebd65d355236d | UNDERPOWERED |
| sspec_1df124b26123342e8fb546f5 | trade_date_block_shuffle | 9193 | BLOCKED | False | True | surrun_4427de1779f4e00798d6f619 | UNDERPOWERED |
| sspec_1df124b26123342e8fb546f5 | trade_date_block_shuffle | 9194 | BLOCKED | False | True | surrun_68e77e63a69732d3e1464db1 | UNDERPOWERED |
| sspec_bd3a4c162a8ba10801bacaa9 | trade_date_block_shuffle | 9195 | BLOCKED | False | True | surrun_c29ea3b852a51ac74a85b5b2 | UNDERPOWERED |
| sspec_bd3a4c162a8ba10801bacaa9 | trade_date_block_shuffle | 9196 | BLOCKED | False | True | surrun_abda7ea414921e327c9f8ccb | UNDERPOWERED |
| sspec_bd3a4c162a8ba10801bacaa9 | trade_date_block_shuffle | 9197 | BLOCKED | False | True | surrun_115dbbf0d9a6ce47b480e4a1 | UNDERPOWERED |
| sspec_1f1b33e1b9c95811cf32c54b | trade_date_block_shuffle | 9198 | BLOCKED | False | True | surrun_f8dcd363b4a36410fac692fe | UNDERPOWERED |
| sspec_1f1b33e1b9c95811cf32c54b | trade_date_block_shuffle | 9199 | BLOCKED | False | True | surrun_6f129307968b2c866a84266e | UNDERPOWERED |
| sspec_1f1b33e1b9c95811cf32c54b | trade_date_block_shuffle | 9200 | BLOCKED | False | True | surrun_20e280a0e4b8748381ae0f90 | UNDERPOWERED |
| sspec_301e12b1db1cbba83b9a2106 | trade_date_block_shuffle | 9201 | BLOCKED | False | True | surrun_9fdcd99b562392ad9b26dc0c | UNDERPOWERED |
| sspec_301e12b1db1cbba83b9a2106 | trade_date_block_shuffle | 9202 | BLOCKED | False | True | surrun_4e6db3fdc05ca5eed6e5b8e3 | UNDERPOWERED |
| sspec_301e12b1db1cbba83b9a2106 | trade_date_block_shuffle | 9203 | BLOCKED | False | True | surrun_ad90d9af9c4b9a94a2289c12 | UNDERPOWERED |
| sspec_1ee6ecda9a3bf1d955553efe | trade_date_block_shuffle | 9204 | BLOCKED | False | True | surrun_8be1ac3bce53fb723e629313 | UNDERPOWERED |
| sspec_1ee6ecda9a3bf1d955553efe | trade_date_block_shuffle | 9205 | BLOCKED | False | True | surrun_50ba6a2b69fb60802bb6776d | UNDERPOWERED |
| sspec_1ee6ecda9a3bf1d955553efe | trade_date_block_shuffle | 9206 | BLOCKED | False | True | surrun_a8cebc413b34ba7cf45b3056 | UNDERPOWERED |
| sspec_a579cbf1af87e63b4f7220e2 | trade_date_block_shuffle | 9207 | BLOCKED | False | False | surrun_97b3c1e02b65f5bef1c76290 | UNDERPOWERED |
| sspec_a579cbf1af87e63b4f7220e2 | trade_date_block_shuffle | 9208 | BLOCKED | False | False | surrun_519b987569f00ccc7984865a | UNDERPOWERED |
| sspec_a579cbf1af87e63b4f7220e2 | trade_date_block_shuffle | 9209 | BLOCKED | False | False | surrun_cfdfda0492a1daad81bc2312 | UNDERPOWERED |
| sspec_af967d49fa45ef55b85fb676 | trade_date_block_shuffle | 9210 | BLOCKED | False | True | surrun_1ae1e0c204c7260326311c81 | UNDERPOWERED |
| sspec_af967d49fa45ef55b85fb676 | trade_date_block_shuffle | 9211 | BLOCKED | False | True | surrun_31050e3dd102b34ffc38627f | UNDERPOWERED |
| sspec_af967d49fa45ef55b85fb676 | trade_date_block_shuffle | 9212 | BLOCKED | False | True | surrun_0c482859c302ddd3dc1684b4 | UNDERPOWERED |
| sspec_4281d5df1d6b2fe91b6504f8 | trade_date_block_shuffle | 9213 | BLOCKED | False | True | surrun_1488d16e056aa2bdda4add57 | UNDERPOWERED |
| sspec_4281d5df1d6b2fe91b6504f8 | trade_date_block_shuffle | 9214 | BLOCKED | False | True | surrun_43e9361dff8245d99347453f | UNDERPOWERED |
| sspec_4281d5df1d6b2fe91b6504f8 | trade_date_block_shuffle | 9215 | BLOCKED | False | True | surrun_9da94e79f3376df81155707c | UNDERPOWERED |
| sspec_b502e277be4ca87d38417886 | trade_date_block_shuffle | 9216 | BLOCKED | False | True | surrun_9d7b4d3d3f22880369885378 | UNDERPOWERED |
| sspec_b502e277be4ca87d38417886 | trade_date_block_shuffle | 9217 | BLOCKED | False | True | surrun_d717a2ef029482f71a8b5391 | UNDERPOWERED |
| sspec_b502e277be4ca87d38417886 | trade_date_block_shuffle | 9218 | BLOCKED | False | True | surrun_5048e991fa42655c10a9d1b4 | UNDERPOWERED |
| sspec_b4b27ebccefebbfb95377bc9 | trade_date_block_shuffle | 9219 | BLOCKED | False | True | surrun_bf5a28e55976bcf72d2b8499 | UNDERPOWERED |
| sspec_b4b27ebccefebbfb95377bc9 | trade_date_block_shuffle | 9220 | BLOCKED | False | True | surrun_6bc4e63e1b2446adc7851aee | UNDERPOWERED |
| sspec_b4b27ebccefebbfb95377bc9 | trade_date_block_shuffle | 9221 | BLOCKED | False | True | surrun_6cebb92f8e49d276730d0d2b | UNDERPOWERED |
| sspec_2a7e821e8cfe8e0338c4e09d | trade_date_block_shuffle | 9222 | BLOCKED | False | True | surrun_e387e176c76bc4903ef3b5b2 | UNDERPOWERED |
| sspec_2a7e821e8cfe8e0338c4e09d | trade_date_block_shuffle | 9223 | BLOCKED | False | True | surrun_1e811721bb5c73f035cd1fe1 | UNDERPOWERED |
| sspec_2a7e821e8cfe8e0338c4e09d | trade_date_block_shuffle | 9224 | BLOCKED | False | True | surrun_151e3600ee1b9147a709f34a | UNDERPOWERED |
| sspec_8ad9023ec33b2254735808a2 | trade_date_block_shuffle | 9225 | BLOCKED | False | False | surrun_4cf125d3a08acde71dceecfe | UNDERPOWERED |
| sspec_8ad9023ec33b2254735808a2 | trade_date_block_shuffle | 9226 | BLOCKED | False | False | surrun_ac357b92d679d2a30bf21294 | UNDERPOWERED |
| sspec_8ad9023ec33b2254735808a2 | trade_date_block_shuffle | 9227 | BLOCKED | False | False | surrun_3ef25e955881ff0401014087 | UNDERPOWERED |
| sspec_a70ade9e0d5fdda6b3e9feb8 | trade_date_block_shuffle | 9228 | BLOCKED | False | True | surrun_8e588aa4ff2344205e769433 | UNDERPOWERED |
| sspec_a70ade9e0d5fdda6b3e9feb8 | trade_date_block_shuffle | 9229 | BLOCKED | False | True | surrun_7ca7aefe7f74dfd107d1920b | UNDERPOWERED |
| sspec_a70ade9e0d5fdda6b3e9feb8 | trade_date_block_shuffle | 9230 | BLOCKED | False | True | surrun_cf87858bd595a62282e36f3a | UNDERPOWERED |
| sspec_3d223cf0b0c18bdcf28e63b6 | trade_date_block_shuffle | 9231 | BLOCKED | False | True | surrun_47fc16b7cc02d5b10852572c | UNDERPOWERED |
| sspec_3d223cf0b0c18bdcf28e63b6 | trade_date_block_shuffle | 9232 | BLOCKED | False | True | surrun_843bf770aace7835fed80cfc | UNDERPOWERED |
| sspec_3d223cf0b0c18bdcf28e63b6 | trade_date_block_shuffle | 9233 | BLOCKED | False | True | surrun_e70193ba1ec5d127cd4f2f13 | UNDERPOWERED |
| sspec_0e3947eeb8f43f5c9ee510ff | trade_date_block_shuffle | 9234 | BLOCKED | False | True | surrun_afc67c3b22440269a2e08407 | UNDERPOWERED |
| sspec_0e3947eeb8f43f5c9ee510ff | trade_date_block_shuffle | 9235 | BLOCKED | False | True | surrun_5cd866ade7b0a1537cab07bc | UNDERPOWERED |
| sspec_0e3947eeb8f43f5c9ee510ff | trade_date_block_shuffle | 9236 | BLOCKED | False | True | surrun_cdf75c690eec64fb1c1cdd85 | UNDERPOWERED |
| sspec_aa1c679817ea63ed7e62befe | trade_date_block_shuffle | 9237 | BLOCKED | False | True | surrun_1559677f2e8942827ee1efa4 | UNDERPOWERED |
| sspec_aa1c679817ea63ed7e62befe | trade_date_block_shuffle | 9238 | BLOCKED | False | True | surrun_2b3e8f818ef126d374e3489b | UNDERPOWERED |
| sspec_aa1c679817ea63ed7e62befe | trade_date_block_shuffle | 9239 | BLOCKED | False | True | surrun_57bf50b6514aa2ebf29a73f6 | UNDERPOWERED |
| sspec_2545d6c71d2e14cf44865f53 | trade_date_block_shuffle | 9240 | BLOCKED | False | True | surrun_b1c189c55e402ba3c92428a7 | UNDERPOWERED |
| sspec_2545d6c71d2e14cf44865f53 | trade_date_block_shuffle | 9241 | BLOCKED | False | True | surrun_f70bfd47e4aa664620db427d | UNDERPOWERED |
| sspec_2545d6c71d2e14cf44865f53 | trade_date_block_shuffle | 9242 | BLOCKED | False | True | surrun_c08d1c46174f42d66f68cef8 | UNDERPOWERED |
| sspec_52fe4c8c50f748803ea8e053 | trade_date_block_shuffle | 9243 | BLOCKED | False | False | surrun_aa660359e2b7beceba51e853 | UNDERPOWERED |
| sspec_52fe4c8c50f748803ea8e053 | trade_date_block_shuffle | 9244 | BLOCKED | False | False | surrun_d8b7791fdfd387d54dd0e284 | UNDERPOWERED |
| sspec_52fe4c8c50f748803ea8e053 | trade_date_block_shuffle | 9245 | BLOCKED | False | False | surrun_f9151e0a87ecb8681f4a3023 | UNDERPOWERED |
| sspec_906538aa4c237f298a69dae9 | trade_date_block_shuffle | 9246 | BLOCKED | False | True | surrun_38339e4b7495b0a438dfe3d2 | UNDERPOWERED |
| sspec_906538aa4c237f298a69dae9 | trade_date_block_shuffle | 9247 | BLOCKED | False | True | surrun_6c0d5ac8819732d4e55bbc8f | UNDERPOWERED |
| sspec_906538aa4c237f298a69dae9 | trade_date_block_shuffle | 9248 | BLOCKED | False | True | surrun_a41636d186bd09041e8e8914 | UNDERPOWERED |
| sspec_bd958d81b3d03af639fb80d6 | trade_date_block_shuffle | 9249 | BLOCKED | False | True | surrun_248f9c7dd7a9152649783130 | UNDERPOWERED |
| sspec_bd958d81b3d03af639fb80d6 | trade_date_block_shuffle | 9250 | BLOCKED | False | True | surrun_2ec05b3a1064ab48c2d106ba | UNDERPOWERED |
| sspec_bd958d81b3d03af639fb80d6 | trade_date_block_shuffle | 9251 | BLOCKED | False | True | surrun_c4ed0d01fef4c70822789b17 | UNDERPOWERED |
| sspec_d5179015d7faddeeb88dcde2 | trade_date_block_shuffle | 9252 | BLOCKED | False | True | surrun_c77f88bc4e98aba45589a4e9 | UNDERPOWERED |
| sspec_d5179015d7faddeeb88dcde2 | trade_date_block_shuffle | 9253 | BLOCKED | False | True | surrun_83b820ccecf45a35724c217f | UNDERPOWERED |
| sspec_d5179015d7faddeeb88dcde2 | trade_date_block_shuffle | 9254 | BLOCKED | False | True | surrun_0b7936eca2d52e96107c492f | UNDERPOWERED |
| sspec_4c52ee84f7192b03cbb0f9f4 | trade_date_block_shuffle | 9255 | BLOCKED | False | True | surrun_dbdc38cbe0401bb074df95a8 | UNDERPOWERED |
| sspec_4c52ee84f7192b03cbb0f9f4 | trade_date_block_shuffle | 9256 | BLOCKED | False | True | surrun_34da211ce1d0da474eb9f8f8 | UNDERPOWERED |
| sspec_4c52ee84f7192b03cbb0f9f4 | trade_date_block_shuffle | 9257 | BLOCKED | False | True | surrun_f9d95071e8c3dcfdcb8dd398 | UNDERPOWERED |
| sspec_fc0422b844bd4f93d497f4d1 | trade_date_block_shuffle | 9258 | BLOCKED | False | True | surrun_e072537336bd8d2cae9e054f | UNDERPOWERED |
| sspec_fc0422b844bd4f93d497f4d1 | trade_date_block_shuffle | 9259 | BLOCKED | False | True | surrun_099d98a760343b1c47aaa24b | UNDERPOWERED |
| sspec_fc0422b844bd4f93d497f4d1 | trade_date_block_shuffle | 9260 | BLOCKED | False | True | surrun_c3a94a3bb7e16b3f20dda540 | UNDERPOWERED |
| sspec_266b2582ea3bc57e083b4b1e | trade_date_block_shuffle | 9261 | BLOCKED | False | False | surrun_5582935280edb614467680e7 | UNDERPOWERED |
| sspec_266b2582ea3bc57e083b4b1e | trade_date_block_shuffle | 9262 | BLOCKED | False | False | surrun_1f3513a322937dcda56e36bf | UNDERPOWERED |
| sspec_266b2582ea3bc57e083b4b1e | trade_date_block_shuffle | 9263 | BLOCKED | False | False | surrun_3e5a2ed942041727537476ad | UNDERPOWERED |
| sspec_9ab1457ee56a433f4184a970 | trade_date_block_shuffle | 9264 | BLOCKED | False | True | surrun_27d9798ca3eecb355fcdc2c7 | UNDERPOWERED |
| sspec_9ab1457ee56a433f4184a970 | trade_date_block_shuffle | 9265 | BLOCKED | False | True | surrun_69401241fa5c08743587b099 | UNDERPOWERED |
| sspec_9ab1457ee56a433f4184a970 | trade_date_block_shuffle | 9266 | BLOCKED | False | True | surrun_d231cc2177ca58a0b5ff4e86 | UNDERPOWERED |
| sspec_9edfecd6f2a4082cfe787a40 | trade_date_block_shuffle | 9267 | BLOCKED | False | True | surrun_df5930b407882f56c3952e8f | UNDERPOWERED |
| sspec_9edfecd6f2a4082cfe787a40 | trade_date_block_shuffle | 9268 | BLOCKED | False | True | surrun_0431381f3faea8b8a425257f | UNDERPOWERED |
| sspec_9edfecd6f2a4082cfe787a40 | trade_date_block_shuffle | 9269 | BLOCKED | False | True | surrun_f2ef121b676d805771a7945a | UNDERPOWERED |
| sspec_b2bd797a50aa4bfb016ce0e2 | trade_date_block_shuffle | 9270 | BLOCKED | False | True | surrun_a0d806a9912baae07e1cceb5 | UNDERPOWERED |
| sspec_b2bd797a50aa4bfb016ce0e2 | trade_date_block_shuffle | 9271 | BLOCKED | False | True | surrun_79f475f1a3d720ab60d96389 | UNDERPOWERED |
| sspec_b2bd797a50aa4bfb016ce0e2 | trade_date_block_shuffle | 9272 | BLOCKED | False | True | surrun_530cb9819b5fbd0ff686afba | UNDERPOWERED |
| sspec_6d77b448d271da92905c259f | trade_date_block_shuffle | 9273 | BLOCKED | False | True | surrun_6df9713f30a226c481cbae07 | UNDERPOWERED |
| sspec_6d77b448d271da92905c259f | trade_date_block_shuffle | 9274 | BLOCKED | False | True | surrun_ea49434db3855c2d63e3de15 | UNDERPOWERED |
| sspec_6d77b448d271da92905c259f | trade_date_block_shuffle | 9275 | BLOCKED | False | True | surrun_acd8c4275367e60df3b4c707 | UNDERPOWERED |
| sspec_56b36be15fe92226fdc753d0 | trade_date_block_shuffle | 9276 | BLOCKED | False | True | surrun_612a3ff3a9064bb45e87ecbd | UNDERPOWERED |
| sspec_56b36be15fe92226fdc753d0 | trade_date_block_shuffle | 9277 | BLOCKED | False | True | surrun_2beed4b32b8e0ef6d0bc57d8 | UNDERPOWERED |
| sspec_56b36be15fe92226fdc753d0 | trade_date_block_shuffle | 9278 | BLOCKED | False | True | surrun_dc61c405efbe6b6ef961745c | UNDERPOWERED |
| sspec_dbd6f3316ed1bef876603a0b | trade_date_block_shuffle | 9279 | BLOCKED | False | False | surrun_7fd9d1cb1830c1980328f51a | UNDERPOWERED |
| sspec_dbd6f3316ed1bef876603a0b | trade_date_block_shuffle | 9280 | BLOCKED | False | False | surrun_a0a3e9cbdf05cd1a0e6ab3fd | UNDERPOWERED |
| sspec_dbd6f3316ed1bef876603a0b | trade_date_block_shuffle | 9281 | BLOCKED | False | False | surrun_6764ccc0f09ec4ca7b48f7db | UNDERPOWERED |
| sspec_ee08e420765f3ac974b34592 | trade_date_block_shuffle | 9282 | BLOCKED | False | True | surrun_eecf846ea04d91fc51734bee | UNDERPOWERED |
| sspec_ee08e420765f3ac974b34592 | trade_date_block_shuffle | 9283 | BLOCKED | False | True | surrun_e677a02f79be311f7188d27b | UNDERPOWERED |
| sspec_ee08e420765f3ac974b34592 | trade_date_block_shuffle | 9284 | BLOCKED | False | True | surrun_33f6d863ce495aeedafe33b2 | UNDERPOWERED |
| sspec_38fd9e95dced1b5c59555f8e | trade_date_block_shuffle | 9285 | BLOCKED | False | True | surrun_b0ebabef1ae0574e5668590d | UNDERPOWERED |
| sspec_38fd9e95dced1b5c59555f8e | trade_date_block_shuffle | 9286 | BLOCKED | False | True | surrun_85a380101f5162c85c258f39 | UNDERPOWERED |
| sspec_38fd9e95dced1b5c59555f8e | trade_date_block_shuffle | 9287 | BLOCKED | False | True | surrun_c0610b4d3c4d8a04facdf210 | UNDERPOWERED |
| sspec_bcf919f46741213c2f4a1c49 | trade_date_block_shuffle | 9288 | BLOCKED | False | True | surrun_8b90d051dbafe3e95bbf220b | UNDERPOWERED |
| sspec_bcf919f46741213c2f4a1c49 | trade_date_block_shuffle | 9289 | BLOCKED | False | True | surrun_6250b24a19eba1c38a5169d9 | UNDERPOWERED |
| sspec_bcf919f46741213c2f4a1c49 | trade_date_block_shuffle | 9290 | BLOCKED | False | True | surrun_cbfe1bae3dc4ef6a47057fdc | UNDERPOWERED |
| sspec_daa74863126dc5d1d2fe9b65 | trade_date_block_shuffle | 9291 | BLOCKED | False | True | surrun_3b85a3f7a70bd21a1616d2f4 | UNDERPOWERED |
| sspec_daa74863126dc5d1d2fe9b65 | trade_date_block_shuffle | 9292 | BLOCKED | False | True | surrun_9951871e3f05915a1b07d43a | UNDERPOWERED |
| sspec_daa74863126dc5d1d2fe9b65 | trade_date_block_shuffle | 9293 | BLOCKED | False | True | surrun_2ae66715fc54fa03973d62d7 | UNDERPOWERED |
| sspec_cf05e6c5ca7e43d6050aa3fc | trade_date_block_shuffle | 9294 | BLOCKED | False | True | surrun_35b92af0d8203a5551e4e415 | UNDERPOWERED |
| sspec_cf05e6c5ca7e43d6050aa3fc | trade_date_block_shuffle | 9295 | BLOCKED | False | True | surrun_115021678eddd2ebfea1116d | UNDERPOWERED |
| sspec_cf05e6c5ca7e43d6050aa3fc | trade_date_block_shuffle | 9296 | BLOCKED | False | True | surrun_a533b4c08cfa2269aabce812 | UNDERPOWERED |
| sspec_e8fe071c662ff3bf070405f8 | trade_date_block_shuffle | 9297 | BLOCKED | False | False | surrun_77972090659340ad57545b38 | UNDERPOWERED |
| sspec_e8fe071c662ff3bf070405f8 | trade_date_block_shuffle | 9298 | BLOCKED | False | False | surrun_c614a978882532fe67fd8eed | UNDERPOWERED |
| sspec_e8fe071c662ff3bf070405f8 | trade_date_block_shuffle | 9299 | BLOCKED | False | False | surrun_11ea4157c62c68773be7f3b6 | UNDERPOWERED |
| sspec_04a2df8739a0cc17b48da8fe | trade_date_block_shuffle | 9300 | BLOCKED | False | True | surrun_e28a60cd90776bda6a18f863 | UNDERPOWERED |
| sspec_04a2df8739a0cc17b48da8fe | trade_date_block_shuffle | 9301 | BLOCKED | False | True | surrun_b5fc4459f04882d97dce451e | UNDERPOWERED |
| sspec_04a2df8739a0cc17b48da8fe | trade_date_block_shuffle | 9302 | BLOCKED | False | True | surrun_2d7ae351ab044321007fac97 | UNDERPOWERED |
| sspec_127c129af9d05112fc66ba6a | trade_date_block_shuffle | 9303 | BLOCKED | False | True | surrun_03962bafe69cac338433b2bc | UNDERPOWERED |
| sspec_127c129af9d05112fc66ba6a | trade_date_block_shuffle | 9304 | BLOCKED | False | True | surrun_a7e9ae972c4ee1d924af20ed | UNDERPOWERED |
| sspec_127c129af9d05112fc66ba6a | trade_date_block_shuffle | 9305 | BLOCKED | False | True | surrun_e101f0f27f695e626c7c09fe | UNDERPOWERED |
| sspec_f91da9fd1dee2cf6ab22a683 | trade_date_block_shuffle | 9306 | BLOCKED | False | True | surrun_031a1a9a4a1acff4e34cc261 | UNDERPOWERED |
| sspec_f91da9fd1dee2cf6ab22a683 | trade_date_block_shuffle | 9307 | BLOCKED | False | True | surrun_a31f7a783c54b59e127061bc | UNDERPOWERED |
| sspec_f91da9fd1dee2cf6ab22a683 | trade_date_block_shuffle | 9308 | BLOCKED | False | True | surrun_2f1da7a0633106d667ceeb60 | UNDERPOWERED |
| sspec_8d138227ba78ba8cbf39e911 | trade_date_block_shuffle | 9309 | BLOCKED | False | True | surrun_dd94392bc60c95e245278c60 | UNDERPOWERED |
| sspec_8d138227ba78ba8cbf39e911 | trade_date_block_shuffle | 9310 | BLOCKED | False | True | surrun_da78ba80c07f84e7a1f37109 | UNDERPOWERED |
| sspec_8d138227ba78ba8cbf39e911 | trade_date_block_shuffle | 9311 | BLOCKED | False | True | surrun_b9391aee274b51ec59c7e052 | UNDERPOWERED |
| sspec_8e77d8eec760215ec7ab820e | trade_date_block_shuffle | 9312 | BLOCKED | False | True | surrun_8018f744b4ac06548541c9fd | UNDERPOWERED |
| sspec_8e77d8eec760215ec7ab820e | trade_date_block_shuffle | 9313 | BLOCKED | False | True | surrun_a1e02ee0116b11365dd4465b | UNDERPOWERED |
| sspec_8e77d8eec760215ec7ab820e | trade_date_block_shuffle | 9314 | BLOCKED | False | True | surrun_24ee6aaecf88969dcd4bea62 | UNDERPOWERED |
| sspec_ac9d363d2b436f470e8d8ee3 | trade_date_block_shuffle | 9315 | BLOCKED | False | False | surrun_ab8814a1b73cc6da11e65d60 | UNDERPOWERED |
| sspec_ac9d363d2b436f470e8d8ee3 | trade_date_block_shuffle | 9316 | BLOCKED | False | False | surrun_9efa50cde004dd67d41b8d02 | UNDERPOWERED |
| sspec_ac9d363d2b436f470e8d8ee3 | trade_date_block_shuffle | 9317 | BLOCKED | False | False | surrun_6461cb5c97a22a3dbe368b50 | UNDERPOWERED |
| sspec_6f5f81332c4b9e51a077ab12 | trade_date_block_shuffle | 9318 | BLOCKED | False | True | surrun_2dc039e1048019d2a47723d6 | UNDERPOWERED |
| sspec_6f5f81332c4b9e51a077ab12 | trade_date_block_shuffle | 9319 | BLOCKED | False | True | surrun_aa4b664094bd643e148b6570 | UNDERPOWERED |
| sspec_6f5f81332c4b9e51a077ab12 | trade_date_block_shuffle | 9320 | BLOCKED | False | True | surrun_681a5b58f6891e1bfe5831a7 | UNDERPOWERED |
| sspec_939b09c440e48b973655ac7a | trade_date_block_shuffle | 9321 | BLOCKED | False | True | surrun_8f0eec95585ec297010a41f5 | UNDERPOWERED |
| sspec_939b09c440e48b973655ac7a | trade_date_block_shuffle | 9322 | BLOCKED | False | True | surrun_4911bfed7e6c55f6b96680b6 | UNDERPOWERED |
| sspec_939b09c440e48b973655ac7a | trade_date_block_shuffle | 9323 | BLOCKED | False | True | surrun_b8601b09e91824146404918b | UNDERPOWERED |
| sspec_6f3194d08eeca0085661f8b4 | trade_date_block_shuffle | 9324 | BLOCKED | False | True | surrun_efca65ff6f2beb4f17002f66 | UNDERPOWERED |
| sspec_6f3194d08eeca0085661f8b4 | trade_date_block_shuffle | 9325 | BLOCKED | False | True | surrun_ebc2e06f2059d8ac7c87add6 | UNDERPOWERED |
| sspec_6f3194d08eeca0085661f8b4 | trade_date_block_shuffle | 9326 | BLOCKED | False | True | surrun_9949aa74850ca5310a83bb8a | UNDERPOWERED |
| sspec_5fb65a4b05a75b3caa99d2de | trade_date_block_shuffle | 9327 | BLOCKED | False | True | surrun_aac4c7db5132b8426e3ac3ec | UNDERPOWERED |
| sspec_5fb65a4b05a75b3caa99d2de | trade_date_block_shuffle | 9328 | BLOCKED | False | True | surrun_e36e53389f51114effe09528 | UNDERPOWERED |
| sspec_5fb65a4b05a75b3caa99d2de | trade_date_block_shuffle | 9329 | BLOCKED | False | True | surrun_cd210d180ff2338d83c76065 | UNDERPOWERED |
| sspec_082ddde49070511dbd490d9b | trade_date_block_shuffle | 9330 | BLOCKED | False | True | surrun_0722abdc9578214cd97d66f8 | UNDERPOWERED |
| sspec_082ddde49070511dbd490d9b | trade_date_block_shuffle | 9331 | BLOCKED | False | True | surrun_25f058fe88d92a7bd60be55b | UNDERPOWERED |
| sspec_082ddde49070511dbd490d9b | trade_date_block_shuffle | 9332 | BLOCKED | False | True | surrun_cf0e4717320941bf583c34d6 | UNDERPOWERED |
| sspec_de80c2b2edc917743028d32c | trade_date_block_shuffle | 9333 | BLOCKED | False | False | surrun_08c5fe765a8b944fb6fbe2fa | UNDERPOWERED |
| sspec_de80c2b2edc917743028d32c | trade_date_block_shuffle | 9334 | BLOCKED | False | False | surrun_1fceb61508f482cc4251037f | UNDERPOWERED |
| sspec_de80c2b2edc917743028d32c | trade_date_block_shuffle | 9335 | BLOCKED | False | False | surrun_3238bb0df8431afcc22142a7 | UNDERPOWERED |
| sspec_a75cb3c454f8767e94ddee80 | trade_date_block_shuffle | 9336 | BLOCKED | False | True | surrun_725e2f56bed3bdb94915118e | UNDERPOWERED |
| sspec_a75cb3c454f8767e94ddee80 | trade_date_block_shuffle | 9337 | BLOCKED | False | True | surrun_4e3d423f3f49d42decca6e15 | UNDERPOWERED |
| sspec_a75cb3c454f8767e94ddee80 | trade_date_block_shuffle | 9338 | BLOCKED | False | True | surrun_2bf847f5c1aec9e4e8875d10 | UNDERPOWERED |
| sspec_1057a08e3cc08ecfdafe6f48 | trade_date_block_shuffle | 9339 | BLOCKED | False | True | surrun_f1f8dacd8921fc1cd5d33660 | UNDERPOWERED |
| sspec_1057a08e3cc08ecfdafe6f48 | trade_date_block_shuffle | 9340 | BLOCKED | False | True | surrun_f6772197de4c1cfdebc0768a | UNDERPOWERED |
| sspec_1057a08e3cc08ecfdafe6f48 | trade_date_block_shuffle | 9341 | BLOCKED | False | True | surrun_89c2e35daa23cf7b6706ee0e | UNDERPOWERED |
| sspec_940856ef6edb85218ad49390 | trade_date_block_shuffle | 9342 | BLOCKED | False | True | surrun_86d24efbcb51f5d29da518cd | UNDERPOWERED |
| sspec_940856ef6edb85218ad49390 | trade_date_block_shuffle | 9343 | BLOCKED | False | True | surrun_95eb0e041fd789b59133f220 | UNDERPOWERED |
| sspec_940856ef6edb85218ad49390 | trade_date_block_shuffle | 9344 | BLOCKED | False | True | surrun_c979c3e791264326c967dd90 | UNDERPOWERED |
| sspec_161989af873a975826c319c4 | trade_date_block_shuffle | 9345 | BLOCKED | False | True | surrun_315ef77f1a301de19e6931cf | UNDERPOWERED |
| sspec_161989af873a975826c319c4 | trade_date_block_shuffle | 9346 | BLOCKED | False | True | surrun_55449ecd40f6d5207409e37a | UNDERPOWERED |
| sspec_161989af873a975826c319c4 | trade_date_block_shuffle | 9347 | BLOCKED | False | True | surrun_9d82908b78fabdcc7a7aa8d3 | UNDERPOWERED |
| sspec_bbeb958477a1fc89451ddeab | trade_date_block_shuffle | 9348 | BLOCKED | False | True | surrun_f99cb9e973a44f6ed9b5bb9d | UNDERPOWERED |
| sspec_bbeb958477a1fc89451ddeab | trade_date_block_shuffle | 9349 | BLOCKED | False | True | surrun_f077b27794184f3c34fa018b | UNDERPOWERED |
| sspec_bbeb958477a1fc89451ddeab | trade_date_block_shuffle | 9350 | BLOCKED | False | True | surrun_f8f2083dbdf7d772fe90769d | UNDERPOWERED |
| sspec_87fc86a4547aa5303033e553 | trade_date_block_shuffle | 9351 | BLOCKED | False | False | surrun_42fe7040a97500233e3f2e96 | UNDERPOWERED |
| sspec_87fc86a4547aa5303033e553 | trade_date_block_shuffle | 9352 | BLOCKED | False | False | surrun_d4f11661ce105682d0a8d449 | UNDERPOWERED |
| sspec_87fc86a4547aa5303033e553 | trade_date_block_shuffle | 9353 | BLOCKED | False | False | surrun_16d6ed178ece12b57f4db559 | UNDERPOWERED |
| sspec_275870335e86592600d51850 | trade_date_block_shuffle | 9354 | BLOCKED | False | True | surrun_2ec89d9897d75863a3aa6864 | UNDERPOWERED |
| sspec_275870335e86592600d51850 | trade_date_block_shuffle | 9355 | BLOCKED | False | True | surrun_d59ae8901a3740675391fbdb | UNDERPOWERED |
| sspec_275870335e86592600d51850 | trade_date_block_shuffle | 9356 | BLOCKED | False | True | surrun_13a65c9a986df4a7ec4c3083 | UNDERPOWERED |
| sspec_86a27d94f4e7006b8c4676a0 | trade_date_block_shuffle | 9357 | BLOCKED | False | True | surrun_de8a658856a26fcbad22537f | UNDERPOWERED |
| sspec_86a27d94f4e7006b8c4676a0 | trade_date_block_shuffle | 9358 | BLOCKED | False | True | surrun_00643f438ec3dae26d1cf355 | UNDERPOWERED |
| sspec_86a27d94f4e7006b8c4676a0 | trade_date_block_shuffle | 9359 | BLOCKED | False | True | surrun_c26585318d24d9e0181b4e7c | UNDERPOWERED |
| sspec_47eb77fbcd4bd6fd9a52ef54 | trade_date_block_shuffle | 9360 | BLOCKED | False | True | surrun_1babf08efa2b4076e2571793 | UNDERPOWERED |
| sspec_47eb77fbcd4bd6fd9a52ef54 | trade_date_block_shuffle | 9361 | BLOCKED | False | True | surrun_c3da6a190c5ecc48ff85728f | UNDERPOWERED |
| sspec_47eb77fbcd4bd6fd9a52ef54 | trade_date_block_shuffle | 9362 | BLOCKED | False | True | surrun_e65a30cf7aa9594d3576c6be | UNDERPOWERED |
| sspec_d6693d28401596a59eb97669 | trade_date_block_shuffle | 9363 | BLOCKED | False | True | surrun_c88680e3301a90ab935beacd | UNDERPOWERED |
| sspec_d6693d28401596a59eb97669 | trade_date_block_shuffle | 9364 | BLOCKED | False | True | surrun_e3435a6dddd44102a993e555 | UNDERPOWERED |
| sspec_d6693d28401596a59eb97669 | trade_date_block_shuffle | 9365 | BLOCKED | False | True | surrun_055f71f4342ded74034600f2 | UNDERPOWERED |
| sspec_086c78ab31b02489b4731d14 | trade_date_block_shuffle | 9366 | BLOCKED | False | True | surrun_96369eed9f66758182bbdd96 | UNDERPOWERED |
| sspec_086c78ab31b02489b4731d14 | trade_date_block_shuffle | 9367 | BLOCKED | False | True | surrun_503953c12ab0428433b4a720 | UNDERPOWERED |
| sspec_086c78ab31b02489b4731d14 | trade_date_block_shuffle | 9368 | BLOCKED | False | True | surrun_74786c44ee8db07cd3777cf9 | UNDERPOWERED |
| sspec_1c1c862cb092207bfd9b5cf1 | trade_date_block_shuffle | 9369 | BLOCKED | False | False | surrun_04fb48a1305954d631d06f75 | UNDERPOWERED |
| sspec_1c1c862cb092207bfd9b5cf1 | trade_date_block_shuffle | 9370 | BLOCKED | False | False | surrun_f37f4a8dd11b8ac312b42583 | UNDERPOWERED |
| sspec_1c1c862cb092207bfd9b5cf1 | trade_date_block_shuffle | 9371 | BLOCKED | False | False | surrun_3de2fab1f5306c058efcb426 | UNDERPOWERED |
| sspec_311a86fec1da6be4845d0cd1 | trade_date_block_shuffle | 9372 | BLOCKED | False | True | surrun_7bf716dcaa96dd1854c91026 | UNDERPOWERED |
| sspec_311a86fec1da6be4845d0cd1 | trade_date_block_shuffle | 9373 | BLOCKED | False | True | surrun_6ca606fec9a9857a5637c2e5 | UNDERPOWERED |
| sspec_311a86fec1da6be4845d0cd1 | trade_date_block_shuffle | 9374 | BLOCKED | False | True | surrun_284238438db319fc54e0e06f | UNDERPOWERED |
| sspec_d732889738c6e30af89f8979 | trade_date_block_shuffle | 9375 | BLOCKED | False | True | surrun_88d730bef9389f0746e43fe8 | UNDERPOWERED |
| sspec_d732889738c6e30af89f8979 | trade_date_block_shuffle | 9376 | BLOCKED | False | True | surrun_6fa6f61dc32f250bb0acb321 | UNDERPOWERED |
| sspec_d732889738c6e30af89f8979 | trade_date_block_shuffle | 9377 | BLOCKED | False | True | surrun_53d80e5bbe9ee8ec04b73d0c | UNDERPOWERED |
| sspec_a357b1e5e03870e2a92b4670 | trade_date_block_shuffle | 9378 | BLOCKED | False | True | surrun_5cf559036fd58b4a702543f2 | UNDERPOWERED |
| sspec_a357b1e5e03870e2a92b4670 | trade_date_block_shuffle | 9379 | BLOCKED | False | True | surrun_6e97b163fceeb00c878d4491 | UNDERPOWERED |
| sspec_a357b1e5e03870e2a92b4670 | trade_date_block_shuffle | 9380 | BLOCKED | False | True | surrun_b6b881c1d3cf1d54042d10be | UNDERPOWERED |
| sspec_13fc592d52ed884202b5cff0 | trade_date_block_shuffle | 9381 | BLOCKED | False | True | surrun_5f2ec1e8474f26f5ec910da1 | UNDERPOWERED |
| sspec_13fc592d52ed884202b5cff0 | trade_date_block_shuffle | 9382 | BLOCKED | False | True | surrun_a78d12a2ace3b1a80de376ef | UNDERPOWERED |
| sspec_13fc592d52ed884202b5cff0 | trade_date_block_shuffle | 9383 | BLOCKED | False | True | surrun_31a7863d5ed724a40516194c | UNDERPOWERED |
| sspec_052a79991cf1b05d4a9a1de1 | trade_date_block_shuffle | 9384 | BLOCKED | False | True | surrun_773d4a7efc73c8cb5c32465f | UNDERPOWERED |
| sspec_052a79991cf1b05d4a9a1de1 | trade_date_block_shuffle | 9385 | BLOCKED | False | True | surrun_5e1d44bc83528e5900422a4a | UNDERPOWERED |
| sspec_052a79991cf1b05d4a9a1de1 | trade_date_block_shuffle | 9386 | BLOCKED | False | True | surrun_9dbb349e05e1b4efedde2db4 | UNDERPOWERED |
| sspec_8165de75ec50096ec9ee007c | trade_date_block_shuffle | 9387 | BLOCKED | False | False | surrun_e293a77a57f82a3abf7de3af | UNDERPOWERED |
| sspec_8165de75ec50096ec9ee007c | trade_date_block_shuffle | 9388 | BLOCKED | False | False | surrun_1073f9b56e5f2e233b0ee0c1 | UNDERPOWERED |
| sspec_8165de75ec50096ec9ee007c | trade_date_block_shuffle | 9389 | BLOCKED | False | False | surrun_4762d5df3637276189255ee6 | UNDERPOWERED |
| sspec_42c51db6a9e7b71fb4c73838 | trade_date_block_shuffle | 9390 | BLOCKED | False | True | surrun_cfe97ab9b65cde348c9acb4d | UNDERPOWERED |
| sspec_42c51db6a9e7b71fb4c73838 | trade_date_block_shuffle | 9391 | BLOCKED | False | True | surrun_7ef7ba803dedb5906847b26f | UNDERPOWERED |
| sspec_42c51db6a9e7b71fb4c73838 | trade_date_block_shuffle | 9392 | BLOCKED | False | True | surrun_4a75e9e08cc7b985c4e4b813 | UNDERPOWERED |
| sspec_1103980d45370aae6701e349 | trade_date_block_shuffle | 9393 | BLOCKED | False | True | surrun_a98775adbbbd533d227e93df | UNDERPOWERED |
| sspec_1103980d45370aae6701e349 | trade_date_block_shuffle | 9394 | BLOCKED | False | True | surrun_57b0a7fea7174237be6297b2 | UNDERPOWERED |
| sspec_1103980d45370aae6701e349 | trade_date_block_shuffle | 9395 | BLOCKED | False | True | surrun_80cb5ce7863dd233257f436e | UNDERPOWERED |
| sspec_296aa7135559fd36871c9013 | trade_date_block_shuffle | 9396 | BLOCKED | False | True | surrun_312db3284affdb4f71674103 | UNDERPOWERED |
| sspec_296aa7135559fd36871c9013 | trade_date_block_shuffle | 9397 | BLOCKED | False | True | surrun_f135a8de895dc2373aaf5107 | UNDERPOWERED |
| sspec_296aa7135559fd36871c9013 | trade_date_block_shuffle | 9398 | BLOCKED | False | True | surrun_910f7c884bd60be99abae6f0 | UNDERPOWERED |
| sspec_a3efbe6cf9248d8af1a6c860 | trade_date_block_shuffle | 9399 | BLOCKED | False | True | surrun_35f6f09bfe112325930694ec | UNDERPOWERED |
| sspec_a3efbe6cf9248d8af1a6c860 | trade_date_block_shuffle | 9400 | BLOCKED | False | True | surrun_2fb573e3f8575b29829b880e | UNDERPOWERED |
| sspec_a3efbe6cf9248d8af1a6c860 | trade_date_block_shuffle | 9401 | BLOCKED | False | True | surrun_e068e70657156255ca09a41a | UNDERPOWERED |
| sspec_60230ee600937f837eb9ac8b | trade_date_block_shuffle | 9402 | BLOCKED | False | True | surrun_7cff9f83d1717099fbd94316 | UNDERPOWERED |
| sspec_60230ee600937f837eb9ac8b | trade_date_block_shuffle | 9403 | BLOCKED | False | True | surrun_5bf07e0a8c4e13c34efd0a71 | UNDERPOWERED |
| sspec_60230ee600937f837eb9ac8b | trade_date_block_shuffle | 9404 | BLOCKED | False | True | surrun_629637f7afea5dccc79a8b64 | UNDERPOWERED |
| sspec_6d52f8c3bd36c0a81fd89009 | trade_date_block_shuffle | 9405 | BLOCKED | False | False | surrun_a4fda8e5b87b9133e2d772bc | UNDERPOWERED |
| sspec_6d52f8c3bd36c0a81fd89009 | trade_date_block_shuffle | 9406 | BLOCKED | False | False | surrun_bf349eacbca782694bc6f0fb | UNDERPOWERED |
| sspec_6d52f8c3bd36c0a81fd89009 | trade_date_block_shuffle | 9407 | BLOCKED | False | False | surrun_cae5778a8effe697bc9b2f08 | UNDERPOWERED |
| sspec_c280d702605e8d161fdcba9a | trade_date_block_shuffle | 9408 | BLOCKED | False | True | surrun_80cec26c05a25e6a0da0c7aa | UNDERPOWERED |
| sspec_c280d702605e8d161fdcba9a | trade_date_block_shuffle | 9409 | BLOCKED | False | True | surrun_489976ebb14d9923f46562c0 | UNDERPOWERED |
| sspec_c280d702605e8d161fdcba9a | trade_date_block_shuffle | 9410 | BLOCKED | False | True | surrun_a5db858d1e7da8fba108754e | UNDERPOWERED |
| sspec_04a8d81bbfd7998662d85571 | trade_date_block_shuffle | 9411 | BLOCKED | False | True | surrun_e693ea19e99c3ecb0fe234ea | UNDERPOWERED |
| sspec_04a8d81bbfd7998662d85571 | trade_date_block_shuffle | 9412 | BLOCKED | False | True | surrun_52555aefdfdb73f62cec6ee6 | UNDERPOWERED |
| sspec_04a8d81bbfd7998662d85571 | trade_date_block_shuffle | 9413 | BLOCKED | False | True | surrun_bd10b14c5ea5e596bae2fb1c | UNDERPOWERED |
| sspec_69f78a1a7473a04f57aee125 | trade_date_block_shuffle | 9414 | BLOCKED | False | True | surrun_61e9fbb7ab55c89c408c20b8 | UNDERPOWERED |
| sspec_69f78a1a7473a04f57aee125 | trade_date_block_shuffle | 9415 | BLOCKED | False | True | surrun_a4395c17974ed79dd826f0f9 | UNDERPOWERED |
| sspec_69f78a1a7473a04f57aee125 | trade_date_block_shuffle | 9416 | BLOCKED | False | True | surrun_652c2ed85db906dd59437029 | UNDERPOWERED |
| sspec_a2c9760321679f58a980bfad | trade_date_block_shuffle | 9417 | BLOCKED | False | True | surrun_2d60c96c562426297b148cad | UNDERPOWERED |
| sspec_a2c9760321679f58a980bfad | trade_date_block_shuffle | 9418 | BLOCKED | False | True | surrun_b9515127194c6abd79b93323 | UNDERPOWERED |
| sspec_a2c9760321679f58a980bfad | trade_date_block_shuffle | 9419 | BLOCKED | False | True | surrun_3ed66d9a1862623abdbfea4b | UNDERPOWERED |
| sspec_7546239329995db0827623eb | trade_date_block_shuffle | 9420 | BLOCKED | False | True | surrun_8fe4d17d58d0eb8af36e94ae | UNDERPOWERED |
| sspec_7546239329995db0827623eb | trade_date_block_shuffle | 9421 | BLOCKED | False | True | surrun_5fbaf97501e87390b9e5c062 | UNDERPOWERED |
| sspec_7546239329995db0827623eb | trade_date_block_shuffle | 9422 | BLOCKED | False | True | surrun_d170d652d3ba763697ca37b8 | UNDERPOWERED |
| sspec_d8be1146f7466118c077d809 | trade_date_block_shuffle | 9423 | BLOCKED | False | False | surrun_be84e6e1640b6092d9456e51 | UNDERPOWERED |
| sspec_d8be1146f7466118c077d809 | trade_date_block_shuffle | 9424 | BLOCKED | False | False | surrun_1401a314510ddedae960ca18 | UNDERPOWERED |
| sspec_d8be1146f7466118c077d809 | trade_date_block_shuffle | 9425 | BLOCKED | False | False | surrun_6b6dbc59efd10048209f4288 | UNDERPOWERED |
| sspec_539236624ffa674c3bb4e40d | trade_date_block_shuffle | 9426 | BLOCKED | False | True | surrun_dfe4f82807c4f34f496fa852 | UNDERPOWERED |
| sspec_539236624ffa674c3bb4e40d | trade_date_block_shuffle | 9427 | BLOCKED | False | True | surrun_877a1d06bd73bee2fe0e2d29 | UNDERPOWERED |
| sspec_539236624ffa674c3bb4e40d | trade_date_block_shuffle | 9428 | BLOCKED | False | True | surrun_497e99aa505a6b0a448dfd2e | UNDERPOWERED |
| sspec_118fd64cad94c8a9151f1f48 | trade_date_block_shuffle | 9429 | BLOCKED | False | True | surrun_ae78a7e534c1d3f93b1c13e1 | UNDERPOWERED |
| sspec_118fd64cad94c8a9151f1f48 | trade_date_block_shuffle | 9430 | BLOCKED | False | True | surrun_a2c9fc8a5573999494713948 | UNDERPOWERED |
| sspec_118fd64cad94c8a9151f1f48 | trade_date_block_shuffle | 9431 | BLOCKED | False | True | surrun_b2da04de167a3528ac8bb7d4 | UNDERPOWERED |
| sspec_71e13870ada9f3439366b396 | trade_date_block_bootstrap | 9432 | BLOCKED | False | True | surrun_daf23359a4b5db908fb723ff | UNDERPOWERED |
| sspec_71e13870ada9f3439366b396 | trade_date_block_bootstrap | 9433 | BLOCKED | False | True | surrun_418c828226a1aed03b406613 | UNDERPOWERED |
| sspec_71e13870ada9f3439366b396 | trade_date_block_bootstrap | 9434 | BLOCKED | False | True | surrun_993e47601fdfd0779897a07c | UNDERPOWERED |
| sspec_088c0c4cab0bb77b3c0db5cc | trade_date_block_bootstrap | 9435 | BLOCKED | False | True | surrun_a2d45463ea8b5dedeafd0169 | UNDERPOWERED |
| sspec_088c0c4cab0bb77b3c0db5cc | trade_date_block_bootstrap | 9436 | BLOCKED | False | True | surrun_c12d21176ae2438e2d8eb4d0 | UNDERPOWERED |
| sspec_088c0c4cab0bb77b3c0db5cc | trade_date_block_bootstrap | 9437 | BLOCKED | False | True | surrun_6eae5e3797499ce8538e4935 | UNDERPOWERED |
| sspec_f92099ee740da509337aabd8 | trade_date_block_bootstrap | 9438 | BLOCKED | False | True | surrun_fc9fbe6a45b0fca5f49f5ebf | UNDERPOWERED |
| sspec_f92099ee740da509337aabd8 | trade_date_block_bootstrap | 9439 | BLOCKED | False | True | surrun_b4e9e208d99d67721136b2f2 | UNDERPOWERED |
| sspec_f92099ee740da509337aabd8 | trade_date_block_bootstrap | 9440 | BLOCKED | False | True | surrun_997cc7d0182de43bc3e00b86 | UNDERPOWERED |
| sspec_f97ad909e3e3bae7cd442eba | trade_date_block_bootstrap | 9441 | BLOCKED | False | False | surrun_d1c4a79952bf330f9e602367 | UNDERPOWERED |
| sspec_f97ad909e3e3bae7cd442eba | trade_date_block_bootstrap | 9442 | BLOCKED | False | False | surrun_7f3fe14c4b97d04050644440 | UNDERPOWERED |
| sspec_f97ad909e3e3bae7cd442eba | trade_date_block_bootstrap | 9443 | BLOCKED | False | False | surrun_67a916a96d2c2027a1a68e4e | UNDERPOWERED |
| sspec_699a13eabc303de9690be6f9 | trade_date_block_bootstrap | 9444 | BLOCKED | False | True | surrun_30ad48a900242aca75664fc6 | UNDERPOWERED |
| sspec_699a13eabc303de9690be6f9 | trade_date_block_bootstrap | 9445 | BLOCKED | False | True | surrun_5981315308ab1debff051263 | UNDERPOWERED |
| sspec_699a13eabc303de9690be6f9 | trade_date_block_bootstrap | 9446 | BLOCKED | False | True | surrun_29fbfed38c2ed3400e7491bc | UNDERPOWERED |
| sspec_9c883e763c74d136d00a4ac9 | trade_date_block_bootstrap | 9447 | BLOCKED | False | True | surrun_8707cb77bb994f759bc7a20c | UNDERPOWERED |
| sspec_9c883e763c74d136d00a4ac9 | trade_date_block_bootstrap | 9448 | BLOCKED | False | True | surrun_6b33a71e133eb968356f0321 | UNDERPOWERED |
| sspec_9c883e763c74d136d00a4ac9 | trade_date_block_bootstrap | 9449 | BLOCKED | False | True | surrun_f7c0a960f112940c30040bf5 | UNDERPOWERED |
| sspec_537b74c57fb77801308ad239 | trade_date_block_bootstrap | 9450 | BLOCKED | False | True | surrun_c50aef5d6578f5df95b2fa13 | UNDERPOWERED |
| sspec_537b74c57fb77801308ad239 | trade_date_block_bootstrap | 9451 | BLOCKED | False | True | surrun_51dc758498191a7d915a45ef | UNDERPOWERED |
| sspec_537b74c57fb77801308ad239 | trade_date_block_bootstrap | 9452 | BLOCKED | False | True | surrun_4dc338589e29b5f825a2e82e | UNDERPOWERED |
| sspec_2c7232f7471bfce087ef899c | trade_date_block_bootstrap | 9453 | BLOCKED | False | True | surrun_e14c63cd48c5731309b1c19c | UNDERPOWERED |
| sspec_2c7232f7471bfce087ef899c | trade_date_block_bootstrap | 9454 | BLOCKED | False | True | surrun_8224879b768f13db72fc4040 | UNDERPOWERED |
| sspec_2c7232f7471bfce087ef899c | trade_date_block_bootstrap | 9455 | BLOCKED | False | True | surrun_e6e2757afbdcea0834e07536 | UNDERPOWERED |
| sspec_dbd173e28cfe2bf0b3b8ebff | trade_date_block_bootstrap | 9456 | BLOCKED | False | True | surrun_7f8f694535c90fb4e2e973a2 | UNDERPOWERED |
| sspec_dbd173e28cfe2bf0b3b8ebff | trade_date_block_bootstrap | 9457 | BLOCKED | False | True | surrun_176a30ffb152afa6d1bcc7f5 | UNDERPOWERED |
| sspec_dbd173e28cfe2bf0b3b8ebff | trade_date_block_bootstrap | 9458 | BLOCKED | False | True | surrun_192cd9b4c587adad7b794808 | UNDERPOWERED |
| sspec_e7c120acb53f6d56e263fadc | trade_date_block_bootstrap | 9459 | BLOCKED | False | False | surrun_75e4910027d1f4dd6c10aa5e | UNDERPOWERED |
| sspec_e7c120acb53f6d56e263fadc | trade_date_block_bootstrap | 9460 | BLOCKED | False | False | surrun_f2de695fb07ffdc5be3abbd2 | UNDERPOWERED |
| sspec_e7c120acb53f6d56e263fadc | trade_date_block_bootstrap | 9461 | BLOCKED | False | False | surrun_7847def472aef8bf9f1245a7 | UNDERPOWERED |
| sspec_386403d215c56b35fcc5b52c | trade_date_block_bootstrap | 9462 | BLOCKED | False | True | surrun_71bf376909eb7ccbb3a23ecc | UNDERPOWERED |
| sspec_386403d215c56b35fcc5b52c | trade_date_block_bootstrap | 9463 | BLOCKED | False | True | surrun_26b2896b6b35ca8748811c45 | UNDERPOWERED |
| sspec_386403d215c56b35fcc5b52c | trade_date_block_bootstrap | 9464 | BLOCKED | False | True | surrun_0d3957173b1a7fdfb415817f | UNDERPOWERED |
| sspec_4ab842f4b76ad2c0b534c503 | trade_date_block_bootstrap | 9465 | BLOCKED | False | True | surrun_7239c341dcf3949058b8d8f5 | UNDERPOWERED |
| sspec_4ab842f4b76ad2c0b534c503 | trade_date_block_bootstrap | 9466 | BLOCKED | False | True | surrun_022a693247e93e942f54e126 | UNDERPOWERED |
| sspec_4ab842f4b76ad2c0b534c503 | trade_date_block_bootstrap | 9467 | BLOCKED | False | True | surrun_27cbf911aad48b61e098018c | UNDERPOWERED |
| sspec_c11497caee78bbf6f34d27db | trade_date_block_bootstrap | 9468 | BLOCKED | False | True | surrun_a35a772e6dfd811b04df8067 | UNDERPOWERED |
| sspec_c11497caee78bbf6f34d27db | trade_date_block_bootstrap | 9469 | BLOCKED | False | True | surrun_7cc3d970a10ee01fef5d4663 | UNDERPOWERED |
| sspec_c11497caee78bbf6f34d27db | trade_date_block_bootstrap | 9470 | BLOCKED | False | True | surrun_4417c448ffa1cb5b55a466fa | UNDERPOWERED |
| sspec_7c0b0284f9f795143b75aea9 | trade_date_block_bootstrap | 9471 | BLOCKED | False | True | surrun_1f795a098eefa00c186de1aa | UNDERPOWERED |
| sspec_7c0b0284f9f795143b75aea9 | trade_date_block_bootstrap | 9472 | BLOCKED | False | True | surrun_7ddbe3bf1612a5a24bd37e0f | UNDERPOWERED |
| sspec_7c0b0284f9f795143b75aea9 | trade_date_block_bootstrap | 9473 | BLOCKED | False | True | surrun_58a6a3207e3b4c56656cc6a1 | UNDERPOWERED |
| sspec_b7693add215b26e0043283b6 | trade_date_block_bootstrap | 9474 | BLOCKED | False | True | surrun_2b7f5b3abf700a0bde26543b | UNDERPOWERED |
| sspec_b7693add215b26e0043283b6 | trade_date_block_bootstrap | 9475 | BLOCKED | False | True | surrun_7080fdfbea5007e37e79b0db | UNDERPOWERED |
| sspec_b7693add215b26e0043283b6 | trade_date_block_bootstrap | 9476 | BLOCKED | False | True | surrun_a9d3a5f25c6c90723ce1682d | UNDERPOWERED |
| sspec_15d04fafd6e3794db2271ebf | trade_date_block_bootstrap | 9477 | BLOCKED | False | False | surrun_54f115d94ee089f8a46fc748 | UNDERPOWERED |
| sspec_15d04fafd6e3794db2271ebf | trade_date_block_bootstrap | 9478 | BLOCKED | False | False | surrun_9d0f982680ee5624f47015b9 | UNDERPOWERED |
| sspec_15d04fafd6e3794db2271ebf | trade_date_block_bootstrap | 9479 | BLOCKED | False | False | surrun_218a41b834996d4c95c5a0de | UNDERPOWERED |
| sspec_110e51c7aa9eb561134b3190 | trade_date_block_bootstrap | 9480 | BLOCKED | False | True | surrun_4d872fed33a521210b68e877 | UNDERPOWERED |
| sspec_110e51c7aa9eb561134b3190 | trade_date_block_bootstrap | 9481 | BLOCKED | False | True | surrun_918cff7906d52f32157b6d42 | UNDERPOWERED |
| sspec_110e51c7aa9eb561134b3190 | trade_date_block_bootstrap | 9482 | BLOCKED | False | True | surrun_8dbddebaa106017c74556943 | UNDERPOWERED |
| sspec_c0c81259945694f00ecf1add | trade_date_block_bootstrap | 9483 | BLOCKED | False | True | surrun_9d4d6741c4f7209236294804 | UNDERPOWERED |
| sspec_c0c81259945694f00ecf1add | trade_date_block_bootstrap | 9484 | BLOCKED | False | True | surrun_91d591d28f0f1e571f16571c | UNDERPOWERED |
| sspec_c0c81259945694f00ecf1add | trade_date_block_bootstrap | 9485 | BLOCKED | False | True | surrun_25c57252d67e129d2b638ecb | UNDERPOWERED |
| sspec_d5c3fdaa393fb21ab395b037 | trade_date_block_bootstrap | 9486 | BLOCKED | False | True | surrun_b48204fe17d443412a786fc6 | UNDERPOWERED |
| sspec_d5c3fdaa393fb21ab395b037 | trade_date_block_bootstrap | 9487 | BLOCKED | False | True | surrun_7b786075d27e5a90d0a7b5d4 | UNDERPOWERED |
| sspec_d5c3fdaa393fb21ab395b037 | trade_date_block_bootstrap | 9488 | BLOCKED | False | True | surrun_916d1597aa2b195a5180d46e | UNDERPOWERED |
| sspec_51984daf0f936e12012b6f9b | trade_date_block_bootstrap | 9489 | BLOCKED | False | True | surrun_3c2372435a85cad1447b2119 | UNDERPOWERED |
| sspec_51984daf0f936e12012b6f9b | trade_date_block_bootstrap | 9490 | BLOCKED | False | True | surrun_817dd6410b45970a7cfa8809 | UNDERPOWERED |
| sspec_51984daf0f936e12012b6f9b | trade_date_block_bootstrap | 9491 | BLOCKED | False | True | surrun_8dfee7395c9feed19bd32c23 | UNDERPOWERED |
| sspec_2c38a886b417233d0f329de4 | trade_date_block_bootstrap | 9492 | BLOCKED | False | True | surrun_843f6a4bdba4d5a7cdfb737e | UNDERPOWERED |
| sspec_2c38a886b417233d0f329de4 | trade_date_block_bootstrap | 9493 | BLOCKED | False | True | surrun_210c7218681f0198c7be0695 | UNDERPOWERED |
| sspec_2c38a886b417233d0f329de4 | trade_date_block_bootstrap | 9494 | BLOCKED | False | True | surrun_cfdddaa6526241aa41d2115b | UNDERPOWERED |
| sspec_673a4ecda99f38d9afc2407d | trade_date_block_bootstrap | 9495 | BLOCKED | False | False | surrun_93cddf785f039456a08368a5 | UNDERPOWERED |
| sspec_673a4ecda99f38d9afc2407d | trade_date_block_bootstrap | 9496 | BLOCKED | False | False | surrun_c857a133c5490c266fd7f3af | UNDERPOWERED |
| sspec_673a4ecda99f38d9afc2407d | trade_date_block_bootstrap | 9497 | BLOCKED | False | False | surrun_14ddb3f35e7d934f445ac193 | UNDERPOWERED |
| sspec_9d3f841efb7e37a1b2f6a4ea | trade_date_block_bootstrap | 9498 | BLOCKED | False | True | surrun_df83af10c20f7daf5d841b6f | UNDERPOWERED |
| sspec_9d3f841efb7e37a1b2f6a4ea | trade_date_block_bootstrap | 9499 | BLOCKED | False | True | surrun_11b42a91439e2449a488cbfd | UNDERPOWERED |
| sspec_9d3f841efb7e37a1b2f6a4ea | trade_date_block_bootstrap | 9500 | BLOCKED | False | True | surrun_edaf0d1076ba08c667e9be7f | UNDERPOWERED |
| sspec_85528ce6713165fc56411d18 | trade_date_block_bootstrap | 9501 | BLOCKED | False | True | surrun_5d8d1246e605b5772246a84a | UNDERPOWERED |
| sspec_85528ce6713165fc56411d18 | trade_date_block_bootstrap | 9502 | BLOCKED | False | True | surrun_2aed13b3078076c433c1147b | UNDERPOWERED |
| sspec_85528ce6713165fc56411d18 | trade_date_block_bootstrap | 9503 | BLOCKED | False | True | surrun_429cab82a81f5ddafa8445af | UNDERPOWERED |
| sspec_612a22a1e3fae57e3fe9be6e | trade_date_block_bootstrap | 9504 | BLOCKED | False | True | surrun_ffc9adee88fc854a81f5b8ec | UNDERPOWERED |
| sspec_612a22a1e3fae57e3fe9be6e | trade_date_block_bootstrap | 9505 | BLOCKED | False | True | surrun_e2f2667db4e525339a52eb99 | UNDERPOWERED |
| sspec_612a22a1e3fae57e3fe9be6e | trade_date_block_bootstrap | 9506 | BLOCKED | False | True | surrun_4122367f1d56ef053696e1a7 | UNDERPOWERED |
| sspec_cf7ac520fcc429b6475439e4 | trade_date_block_bootstrap | 9507 | BLOCKED | False | True | surrun_26d5ac3050b4d48f74ea4ee2 | UNDERPOWERED |
| sspec_cf7ac520fcc429b6475439e4 | trade_date_block_bootstrap | 9508 | BLOCKED | False | True | surrun_87524ad334fa410b59096204 | UNDERPOWERED |
| sspec_cf7ac520fcc429b6475439e4 | trade_date_block_bootstrap | 9509 | BLOCKED | False | True | surrun_4cef15b566f94726bf8eb4f9 | UNDERPOWERED |
| sspec_49147e59ea35c1524af9e45f | trade_date_block_bootstrap | 9510 | BLOCKED | False | True | surrun_aa7ef0774fd842ffa5f94941 | UNDERPOWERED |
| sspec_49147e59ea35c1524af9e45f | trade_date_block_bootstrap | 9511 | BLOCKED | False | True | surrun_cf19cee72aa36f3a059d6356 | UNDERPOWERED |
| sspec_49147e59ea35c1524af9e45f | trade_date_block_bootstrap | 9512 | BLOCKED | False | True | surrun_bd0af8990da7d8d84e633c65 | UNDERPOWERED |
| sspec_7046ae570b393874b90a86dc | trade_date_block_bootstrap | 9513 | BLOCKED | False | False | surrun_a0f22948800a4300360ffde1 | UNDERPOWERED |
| sspec_7046ae570b393874b90a86dc | trade_date_block_bootstrap | 9514 | BLOCKED | False | False | surrun_1c829b113bd29031c3506c93 | UNDERPOWERED |
| sspec_7046ae570b393874b90a86dc | trade_date_block_bootstrap | 9515 | BLOCKED | False | False | surrun_54f0bdd932a006d8fea324d1 | UNDERPOWERED |
| sspec_45e43b7e26bff0f649022dbe | trade_date_block_bootstrap | 9516 | BLOCKED | False | True | surrun_9026fd0ae323887bb279eeda | UNDERPOWERED |
| sspec_45e43b7e26bff0f649022dbe | trade_date_block_bootstrap | 9517 | BLOCKED | False | True | surrun_af7f4a86d954f9c477a56d3d | UNDERPOWERED |
| sspec_45e43b7e26bff0f649022dbe | trade_date_block_bootstrap | 9518 | BLOCKED | False | True | surrun_d0739d1ebd3da68569da08a7 | UNDERPOWERED |
| sspec_1667ddb835e6855009b531b3 | trade_date_block_bootstrap | 9519 | BLOCKED | False | True | surrun_ce0354e22538b85506e6aea8 | UNDERPOWERED |
| sspec_1667ddb835e6855009b531b3 | trade_date_block_bootstrap | 9520 | BLOCKED | False | True | surrun_f4d3a4ce4f6d8551cfda0829 | UNDERPOWERED |
| sspec_1667ddb835e6855009b531b3 | trade_date_block_bootstrap | 9521 | BLOCKED | False | True | surrun_d6dad13aab5a46c37f9d488a | UNDERPOWERED |
| sspec_7ae5f694ea2dae90ef35070a | trade_date_block_bootstrap | 9522 | BLOCKED | False | True | surrun_b9630cdc1944f294107f0f93 | UNDERPOWERED |
| sspec_7ae5f694ea2dae90ef35070a | trade_date_block_bootstrap | 9523 | BLOCKED | False | True | surrun_f5f688d036d325ba050077ff | UNDERPOWERED |
| sspec_7ae5f694ea2dae90ef35070a | trade_date_block_bootstrap | 9524 | BLOCKED | False | True | surrun_f5a4a94177fc0e8c45ccd406 | UNDERPOWERED |
| sspec_5a1389ac8c1ce500c91adca0 | trade_date_block_bootstrap | 9525 | BLOCKED | False | True | surrun_09a43b9b1c2e549724e09926 | UNDERPOWERED |
| sspec_5a1389ac8c1ce500c91adca0 | trade_date_block_bootstrap | 9526 | BLOCKED | False | True | surrun_de222642ffe8dc0bd649d9d8 | UNDERPOWERED |
| sspec_5a1389ac8c1ce500c91adca0 | trade_date_block_bootstrap | 9527 | BLOCKED | False | True | surrun_068b4359a19403e23cff602a | UNDERPOWERED |
| sspec_65e6f5137f49203e67039618 | trade_date_block_bootstrap | 9528 | BLOCKED | False | True | surrun_064298383c583eca3d545081 | UNDERPOWERED |
| sspec_65e6f5137f49203e67039618 | trade_date_block_bootstrap | 9529 | BLOCKED | False | True | surrun_ea36d61a220ea1f5f6a063eb | UNDERPOWERED |
| sspec_65e6f5137f49203e67039618 | trade_date_block_bootstrap | 9530 | BLOCKED | False | True | surrun_02809a9f5e5fd32d2d2d616e | UNDERPOWERED |
| sspec_f0a44f35c13e75f6968eac4e | trade_date_block_bootstrap | 9531 | BLOCKED | False | False | surrun_b25d721a1b4dfb1fa037857e | UNDERPOWERED |
| sspec_f0a44f35c13e75f6968eac4e | trade_date_block_bootstrap | 9532 | BLOCKED | False | False | surrun_aadb0eaaabcde3741a4146e2 | UNDERPOWERED |
| sspec_f0a44f35c13e75f6968eac4e | trade_date_block_bootstrap | 9533 | BLOCKED | False | False | surrun_d139acc8cd49816776086a6a | UNDERPOWERED |
| sspec_3845e486992283683dce9ba3 | trade_date_block_bootstrap | 9534 | BLOCKED | False | True | surrun_4eba24d59364bfd81322397d | UNDERPOWERED |
| sspec_3845e486992283683dce9ba3 | trade_date_block_bootstrap | 9535 | BLOCKED | False | True | surrun_960b60b5359cf4b062d75259 | UNDERPOWERED |
| sspec_3845e486992283683dce9ba3 | trade_date_block_bootstrap | 9536 | BLOCKED | False | True | surrun_295ed9898f50ac96056d43e2 | UNDERPOWERED |
| sspec_3a8306dcf1c29dd56009b781 | trade_date_block_bootstrap | 9537 | BLOCKED | False | True | surrun_8d06883fe1e1be6fc53ada87 | UNDERPOWERED |
| sspec_3a8306dcf1c29dd56009b781 | trade_date_block_bootstrap | 9538 | BLOCKED | False | True | surrun_3055cf57c84820288ca890bf | UNDERPOWERED |
| sspec_3a8306dcf1c29dd56009b781 | trade_date_block_bootstrap | 9539 | BLOCKED | False | True | surrun_61f3680fc3dd3865cc2e921a | UNDERPOWERED |
| sspec_2263d90cd6e363a844b4a8a5 | trade_date_block_bootstrap | 9540 | BLOCKED | False | True | surrun_1f0ca0823d340a8638c2e39a | UNDERPOWERED |
| sspec_2263d90cd6e363a844b4a8a5 | trade_date_block_bootstrap | 9541 | BLOCKED | False | True | surrun_44839949fafa2bfadd1b4284 | UNDERPOWERED |
| sspec_2263d90cd6e363a844b4a8a5 | trade_date_block_bootstrap | 9542 | BLOCKED | False | True | surrun_4541b96807d1bf5bf4477393 | UNDERPOWERED |
| sspec_25dbac39b219301bab1a5177 | trade_date_block_bootstrap | 9543 | BLOCKED | False | True | surrun_e82ed5a82699afd5957221f5 | UNDERPOWERED |
| sspec_25dbac39b219301bab1a5177 | trade_date_block_bootstrap | 9544 | BLOCKED | False | True | surrun_6afc7ff5b4a2dcee52599240 | UNDERPOWERED |
| sspec_25dbac39b219301bab1a5177 | trade_date_block_bootstrap | 9545 | BLOCKED | False | True | surrun_e51a42e199f1f5e27afb7ac3 | UNDERPOWERED |
| sspec_f205ae668f64e67184d42145 | trade_date_block_bootstrap | 9546 | BLOCKED | False | True | surrun_1ff460de46c2fdcf88efcc8d | UNDERPOWERED |
| sspec_f205ae668f64e67184d42145 | trade_date_block_bootstrap | 9547 | BLOCKED | False | True | surrun_763b32dd83b5ff4739fef85f | UNDERPOWERED |
| sspec_f205ae668f64e67184d42145 | trade_date_block_bootstrap | 9548 | BLOCKED | False | True | surrun_c226f3a6181e2896099debca | UNDERPOWERED |
| sspec_29b931a0f343003bbd02d01c | trade_date_block_bootstrap | 9549 | BLOCKED | False | False | surrun_138c07c9334d0462ce4c9f01 | UNDERPOWERED |
| sspec_29b931a0f343003bbd02d01c | trade_date_block_bootstrap | 9550 | BLOCKED | False | False | surrun_941a41349b07ddd52c91b2c3 | UNDERPOWERED |
| sspec_29b931a0f343003bbd02d01c | trade_date_block_bootstrap | 9551 | BLOCKED | False | False | surrun_bb0f605630fc37ca942ed951 | UNDERPOWERED |
| sspec_862924c23856461f929ae080 | trade_date_block_bootstrap | 9552 | BLOCKED | False | True | surrun_bd4236d3479072e76c71555d | UNDERPOWERED |
| sspec_862924c23856461f929ae080 | trade_date_block_bootstrap | 9553 | BLOCKED | False | True | surrun_69b2ba931eaf99f32b5d0b63 | UNDERPOWERED |
| sspec_862924c23856461f929ae080 | trade_date_block_bootstrap | 9554 | BLOCKED | False | True | surrun_803878ca70266905c92a9507 | UNDERPOWERED |
| sspec_bc3d1222efb35bfe10f89929 | trade_date_block_bootstrap | 9555 | BLOCKED | False | True | surrun_51729014c7c6fc278f7e9456 | UNDERPOWERED |
| sspec_bc3d1222efb35bfe10f89929 | trade_date_block_bootstrap | 9556 | BLOCKED | False | True | surrun_dbdaeb0da16909de3a38cf53 | UNDERPOWERED |
| sspec_bc3d1222efb35bfe10f89929 | trade_date_block_bootstrap | 9557 | BLOCKED | False | True | surrun_d7e73cfba295464417f6aa43 | UNDERPOWERED |
| sspec_b7c870f978b38bf3f62a7624 | trade_date_block_bootstrap | 9558 | BLOCKED | False | True | surrun_95fd69eceeec7045180c7323 | UNDERPOWERED |
| sspec_b7c870f978b38bf3f62a7624 | trade_date_block_bootstrap | 9559 | BLOCKED | False | True | surrun_063a25825916354b1271c5ea | UNDERPOWERED |
| sspec_b7c870f978b38bf3f62a7624 | trade_date_block_bootstrap | 9560 | BLOCKED | False | True | surrun_b9817a95ccc9e2d5098e31b9 | UNDERPOWERED |
| sspec_a4d225065125a873eb137d03 | trade_date_block_bootstrap | 9561 | BLOCKED | False | True | surrun_187274065effa55535af8f0d | UNDERPOWERED |
| sspec_a4d225065125a873eb137d03 | trade_date_block_bootstrap | 9562 | BLOCKED | False | True | surrun_10a8822de5c8b7b76417c326 | UNDERPOWERED |
| sspec_a4d225065125a873eb137d03 | trade_date_block_bootstrap | 9563 | BLOCKED | False | True | surrun_7d4ebe98782848319ee58bc5 | UNDERPOWERED |
| sspec_1e25e9de8dba2b24f0e64c47 | trade_date_block_bootstrap | 9564 | BLOCKED | False | True | surrun_7e0a36e0e1a4853d2692feef | UNDERPOWERED |
| sspec_1e25e9de8dba2b24f0e64c47 | trade_date_block_bootstrap | 9565 | BLOCKED | False | True | surrun_f5cbbb9750fa14c18fc3b806 | UNDERPOWERED |
| sspec_1e25e9de8dba2b24f0e64c47 | trade_date_block_bootstrap | 9566 | BLOCKED | False | True | surrun_02b6dbc6c80db6bc57902157 | UNDERPOWERED |
| sspec_71a3aa976b4c193d945945ab | trade_date_block_bootstrap | 9567 | BLOCKED | False | False | surrun_32fae813455c365d9fa200d9 | UNDERPOWERED |
| sspec_71a3aa976b4c193d945945ab | trade_date_block_bootstrap | 9568 | BLOCKED | False | False | surrun_81f98667591f181614b28809 | UNDERPOWERED |
| sspec_71a3aa976b4c193d945945ab | trade_date_block_bootstrap | 9569 | BLOCKED | False | False | surrun_9edc65b4d4d9ce9d193e7b80 | UNDERPOWERED |
| sspec_7d5dad24d016cd9913744df7 | trade_date_block_bootstrap | 9570 | BLOCKED | False | True | surrun_7c7f157a1047b4867fb2a7ab | UNDERPOWERED |
| sspec_7d5dad24d016cd9913744df7 | trade_date_block_bootstrap | 9571 | BLOCKED | False | True | surrun_78d88b7279dc0a85a58635a4 | UNDERPOWERED |
| sspec_7d5dad24d016cd9913744df7 | trade_date_block_bootstrap | 9572 | BLOCKED | False | True | surrun_2e6b9e8d39e23566bd15ae55 | UNDERPOWERED |
| sspec_04e96bf03de43a8dc0759971 | trade_date_block_bootstrap | 9573 | BLOCKED | False | True | surrun_93a7c6ff0554aed8ba1978f2 | UNDERPOWERED |
| sspec_04e96bf03de43a8dc0759971 | trade_date_block_bootstrap | 9574 | BLOCKED | False | True | surrun_75a3834504da945c4e4d0f7f | UNDERPOWERED |
| sspec_04e96bf03de43a8dc0759971 | trade_date_block_bootstrap | 9575 | BLOCKED | False | True | surrun_1d0d9a78b4d3c8e1b5ade8c8 | UNDERPOWERED |
| sspec_a227d866d2a460e84f4836d4 | trade_date_block_bootstrap | 9576 | BLOCKED | False | True | surrun_aa6d6ecba4ae8337887930f4 | UNDERPOWERED |
| sspec_a227d866d2a460e84f4836d4 | trade_date_block_bootstrap | 9577 | BLOCKED | False | True | surrun_67431ad445ff985d89ead09c | UNDERPOWERED |
| sspec_a227d866d2a460e84f4836d4 | trade_date_block_bootstrap | 9578 | BLOCKED | False | True | surrun_942314234494a972c24b22ef | UNDERPOWERED |
| sspec_d9bf8c128f48a5aa14489b6a | trade_date_block_bootstrap | 9579 | BLOCKED | False | True | surrun_b5741c232a6a35b8af906fa8 | UNDERPOWERED |
| sspec_d9bf8c128f48a5aa14489b6a | trade_date_block_bootstrap | 9580 | BLOCKED | False | True | surrun_bdb72436cf7dc3bd5c617e32 | UNDERPOWERED |
| sspec_d9bf8c128f48a5aa14489b6a | trade_date_block_bootstrap | 9581 | BLOCKED | False | True | surrun_c5e110ad5ddf440171b651d7 | UNDERPOWERED |
| sspec_ce04f0a862ee4837d5976f28 | trade_date_block_bootstrap | 9582 | BLOCKED | False | True | surrun_e137045ae675307273baddb8 | UNDERPOWERED |
| sspec_ce04f0a862ee4837d5976f28 | trade_date_block_bootstrap | 9583 | BLOCKED | False | True | surrun_423be630bf8e7cb1af995172 | UNDERPOWERED |
| sspec_ce04f0a862ee4837d5976f28 | trade_date_block_bootstrap | 9584 | BLOCKED | False | True | surrun_c2894efde1692ed31eaa2be0 | UNDERPOWERED |
| sspec_3163751e574ca37179d3396a | trade_date_block_bootstrap | 9585 | BLOCKED | False | False | surrun_adcb0a66916480655dd482cb | UNDERPOWERED |
| sspec_3163751e574ca37179d3396a | trade_date_block_bootstrap | 9586 | BLOCKED | False | False | surrun_941509ce6cb8a49b8a2ccb83 | UNDERPOWERED |
| sspec_3163751e574ca37179d3396a | trade_date_block_bootstrap | 9587 | BLOCKED | False | False | surrun_510eb1b95126cbaa7e7dff4f | UNDERPOWERED |
| sspec_e4408d6ef919c21990034bd0 | trade_date_block_bootstrap | 9588 | BLOCKED | False | True | surrun_89d690e2870ff215f447ddcf | UNDERPOWERED |
| sspec_e4408d6ef919c21990034bd0 | trade_date_block_bootstrap | 9589 | BLOCKED | False | True | surrun_7002f09fcf0dc91d2ccc1185 | UNDERPOWERED |
| sspec_e4408d6ef919c21990034bd0 | trade_date_block_bootstrap | 9590 | BLOCKED | False | True | surrun_08eb65cf1c9e76a3d6182244 | UNDERPOWERED |
| sspec_682011f6aa35bc534d66ae33 | trade_date_block_bootstrap | 9591 | BLOCKED | False | True | surrun_2d96aa5bdb2ad735ccfe9647 | UNDERPOWERED |
| sspec_682011f6aa35bc534d66ae33 | trade_date_block_bootstrap | 9592 | BLOCKED | False | True | surrun_b9c914499261b8b68e11f736 | UNDERPOWERED |
| sspec_682011f6aa35bc534d66ae33 | trade_date_block_bootstrap | 9593 | BLOCKED | False | True | surrun_079ea9c0a73f8541bae44ff9 | UNDERPOWERED |
| sspec_44a8c2364695282be9865b23 | trade_date_block_bootstrap | 9594 | BLOCKED | False | True | surrun_3f24763c7c446bfdb0a9dd89 | UNDERPOWERED |
| sspec_44a8c2364695282be9865b23 | trade_date_block_bootstrap | 9595 | BLOCKED | False | True | surrun_fc4f0987570bde9163ca787a | UNDERPOWERED |
| sspec_44a8c2364695282be9865b23 | trade_date_block_bootstrap | 9596 | BLOCKED | False | True | surrun_9854888b616f6d3ac79574f3 | UNDERPOWERED |
| sspec_5ff3e9f63b2f32c443d11929 | trade_date_block_bootstrap | 9597 | BLOCKED | False | True | surrun_f55bf0eed7f57ef7b62ef4d6 | UNDERPOWERED |
| sspec_5ff3e9f63b2f32c443d11929 | trade_date_block_bootstrap | 9598 | BLOCKED | False | True | surrun_1fa3c895331c7db25f85da2e | UNDERPOWERED |
| sspec_5ff3e9f63b2f32c443d11929 | trade_date_block_bootstrap | 9599 | BLOCKED | False | True | surrun_611ea100f9a113f4f856edf3 | UNDERPOWERED |
| sspec_a0213fc1cf2176738be0b134 | trade_date_block_bootstrap | 9600 | BLOCKED | False | True | surrun_13e23e53495f6692291ca936 | UNDERPOWERED |
| sspec_a0213fc1cf2176738be0b134 | trade_date_block_bootstrap | 9601 | BLOCKED | False | True | surrun_8d9877f1a9449c937d867002 | UNDERPOWERED |
| sspec_a0213fc1cf2176738be0b134 | trade_date_block_bootstrap | 9602 | BLOCKED | False | True | surrun_55f30b9d95903f830d731818 | UNDERPOWERED |
| sspec_297d60252087f608b59ccb3a | trade_date_block_bootstrap | 9603 | BLOCKED | False | False | surrun_bba063b5f6a057038149ecf5 | UNDERPOWERED |
| sspec_297d60252087f608b59ccb3a | trade_date_block_bootstrap | 9604 | BLOCKED | False | False | surrun_21afd7f70334b0e2d73efe2b | UNDERPOWERED |
| sspec_297d60252087f608b59ccb3a | trade_date_block_bootstrap | 9605 | BLOCKED | False | False | surrun_f452ce08fea729c45e2441c9 | UNDERPOWERED |
| sspec_677919c47329048120d6a0a1 | trade_date_block_bootstrap | 9606 | BLOCKED | False | True | surrun_f1ea3b0fa471b80b0163867e | UNDERPOWERED |
| sspec_677919c47329048120d6a0a1 | trade_date_block_bootstrap | 9607 | BLOCKED | False | True | surrun_3064b622fb6752236eecda59 | UNDERPOWERED |
| sspec_677919c47329048120d6a0a1 | trade_date_block_bootstrap | 9608 | BLOCKED | False | True | surrun_38a976977658270aa906aa67 | UNDERPOWERED |
| sspec_c9bd816912f5d0e3062596fd | trade_date_block_bootstrap | 9609 | BLOCKED | False | True | surrun_d342a47261fd072f23f20fec | UNDERPOWERED |
| sspec_c9bd816912f5d0e3062596fd | trade_date_block_bootstrap | 9610 | BLOCKED | False | True | surrun_ace03f2b6281a76a83820f1f | UNDERPOWERED |
| sspec_c9bd816912f5d0e3062596fd | trade_date_block_bootstrap | 9611 | BLOCKED | False | True | surrun_d68204e07b67c2be8a7f0706 | UNDERPOWERED |
| sspec_96b5c59ca85ab728516f3685 | trade_date_block_bootstrap | 9612 | BLOCKED | False | True | surrun_030de7836a9638bdd24aa50e | UNDERPOWERED |
| sspec_96b5c59ca85ab728516f3685 | trade_date_block_bootstrap | 9613 | BLOCKED | False | True | surrun_43bdb6d4b8332bf50a56e2dc | UNDERPOWERED |
| sspec_96b5c59ca85ab728516f3685 | trade_date_block_bootstrap | 9614 | BLOCKED | False | True | surrun_a526c6bdc9b14e5dc1dd8980 | UNDERPOWERED |
| sspec_c53ce1c1bab5dbceded68cca | trade_date_block_bootstrap | 9615 | BLOCKED | False | True | surrun_27fb216edd5c65905cc33c83 | UNDERPOWERED |
| sspec_c53ce1c1bab5dbceded68cca | trade_date_block_bootstrap | 9616 | BLOCKED | False | True | surrun_c41a61ea7a124c923b837328 | UNDERPOWERED |
| sspec_c53ce1c1bab5dbceded68cca | trade_date_block_bootstrap | 9617 | BLOCKED | False | True | surrun_65a0fdd51469d9cf1f7f6849 | UNDERPOWERED |
| sspec_f7fceba9afe46c9f31c564cc | trade_date_block_bootstrap | 9618 | BLOCKED | False | True | surrun_d25501955d065843b8c4c000 | UNDERPOWERED |
| sspec_f7fceba9afe46c9f31c564cc | trade_date_block_bootstrap | 9619 | BLOCKED | False | True | surrun_4263b5e1671d51256a93bdca | UNDERPOWERED |
| sspec_f7fceba9afe46c9f31c564cc | trade_date_block_bootstrap | 9620 | BLOCKED | False | True | surrun_3845a5f8a23f11ff93c8e442 | UNDERPOWERED |
| sspec_db044241ed2a1c38f7be6890 | trade_date_block_bootstrap | 9621 | BLOCKED | False | False | surrun_e02f412f346b3e31b5431f26 | UNDERPOWERED |
| sspec_db044241ed2a1c38f7be6890 | trade_date_block_bootstrap | 9622 | BLOCKED | False | False | surrun_6e60d80db735062b64169e19 | UNDERPOWERED |
| sspec_db044241ed2a1c38f7be6890 | trade_date_block_bootstrap | 9623 | BLOCKED | False | False | surrun_207ba1ca9c360f8ca6be5b33 | UNDERPOWERED |
| sspec_1df124b26123342e8fb546f5 | trade_date_block_bootstrap | 9624 | BLOCKED | False | True | surrun_6ac91ef1dc53afc05668a16f | UNDERPOWERED |
| sspec_1df124b26123342e8fb546f5 | trade_date_block_bootstrap | 9625 | BLOCKED | False | True | surrun_7c7974b5e3866f6561e71569 | UNDERPOWERED |
| sspec_1df124b26123342e8fb546f5 | trade_date_block_bootstrap | 9626 | BLOCKED | False | True | surrun_8d42aee76e101ceb9b8c6a6a | UNDERPOWERED |
| sspec_bd3a4c162a8ba10801bacaa9 | trade_date_block_bootstrap | 9627 | BLOCKED | False | True | surrun_421bdadab9fbcb640ebfd23c | UNDERPOWERED |
| sspec_bd3a4c162a8ba10801bacaa9 | trade_date_block_bootstrap | 9628 | BLOCKED | False | True | surrun_c9fb1c74eebd1c11e6bb3697 | UNDERPOWERED |
| sspec_bd3a4c162a8ba10801bacaa9 | trade_date_block_bootstrap | 9629 | BLOCKED | False | True | surrun_c477bf9435ee4a614f7b6825 | UNDERPOWERED |
| sspec_1f1b33e1b9c95811cf32c54b | trade_date_block_bootstrap | 9630 | BLOCKED | False | True | surrun_3b78318194a030e55ccf5def | UNDERPOWERED |
| sspec_1f1b33e1b9c95811cf32c54b | trade_date_block_bootstrap | 9631 | BLOCKED | False | True | surrun_0d7d2138424ee38bb16444aa | UNDERPOWERED |
| sspec_1f1b33e1b9c95811cf32c54b | trade_date_block_bootstrap | 9632 | BLOCKED | False | True | surrun_d9c044b9c57cae24a3277cab | UNDERPOWERED |
| sspec_301e12b1db1cbba83b9a2106 | trade_date_block_bootstrap | 9633 | BLOCKED | False | True | surrun_f55101d5775c221a71a61328 | UNDERPOWERED |
| sspec_301e12b1db1cbba83b9a2106 | trade_date_block_bootstrap | 9634 | BLOCKED | False | True | surrun_206c8b757adcb1f85ea5067a | UNDERPOWERED |
| sspec_301e12b1db1cbba83b9a2106 | trade_date_block_bootstrap | 9635 | BLOCKED | False | True | surrun_763f6e6308b83fd7d3d726b0 | UNDERPOWERED |
| sspec_1ee6ecda9a3bf1d955553efe | trade_date_block_bootstrap | 9636 | BLOCKED | False | True | surrun_a3aff32713b231f927591ef0 | UNDERPOWERED |
| sspec_1ee6ecda9a3bf1d955553efe | trade_date_block_bootstrap | 9637 | BLOCKED | False | True | surrun_7f88e292d502243bdf886b5c | UNDERPOWERED |
| sspec_1ee6ecda9a3bf1d955553efe | trade_date_block_bootstrap | 9638 | BLOCKED | False | True | surrun_2ae60d4c3c12d436cdc39a49 | UNDERPOWERED |
| sspec_a579cbf1af87e63b4f7220e2 | trade_date_block_bootstrap | 9639 | BLOCKED | False | False | surrun_94584c7ee8fb8e9f863adeb6 | UNDERPOWERED |
| sspec_a579cbf1af87e63b4f7220e2 | trade_date_block_bootstrap | 9640 | BLOCKED | False | False | surrun_3bbb6300c61b072409427ec2 | UNDERPOWERED |
| sspec_a579cbf1af87e63b4f7220e2 | trade_date_block_bootstrap | 9641 | BLOCKED | False | False | surrun_bda90f5276c8cd37e832ff02 | UNDERPOWERED |
| sspec_af967d49fa45ef55b85fb676 | trade_date_block_bootstrap | 9642 | BLOCKED | False | True | surrun_27a12acd15978fe816785228 | UNDERPOWERED |
| sspec_af967d49fa45ef55b85fb676 | trade_date_block_bootstrap | 9643 | BLOCKED | False | True | surrun_4ddfe98bfc82e961198b5c09 | UNDERPOWERED |
| sspec_af967d49fa45ef55b85fb676 | trade_date_block_bootstrap | 9644 | BLOCKED | False | True | surrun_2a64afb25f713a4b0d11b1c6 | UNDERPOWERED |
| sspec_4281d5df1d6b2fe91b6504f8 | trade_date_block_bootstrap | 9645 | BLOCKED | False | True | surrun_686f41ad81101bd6afe702b0 | UNDERPOWERED |
| sspec_4281d5df1d6b2fe91b6504f8 | trade_date_block_bootstrap | 9646 | BLOCKED | False | True | surrun_f91a1699cb01e15dd4baf5b0 | UNDERPOWERED |
| sspec_4281d5df1d6b2fe91b6504f8 | trade_date_block_bootstrap | 9647 | BLOCKED | False | True | surrun_fc4c78095a00566fa830965c | UNDERPOWERED |
| sspec_b502e277be4ca87d38417886 | trade_date_block_bootstrap | 9648 | BLOCKED | False | True | surrun_02ca6a158eef3a4cfe4a1cad | UNDERPOWERED |
| sspec_b502e277be4ca87d38417886 | trade_date_block_bootstrap | 9649 | BLOCKED | False | True | surrun_a07944867e254d21dc08a543 | UNDERPOWERED |
| sspec_b502e277be4ca87d38417886 | trade_date_block_bootstrap | 9650 | BLOCKED | False | True | surrun_e683f09cf742779dec4d3e64 | UNDERPOWERED |
| sspec_b4b27ebccefebbfb95377bc9 | trade_date_block_bootstrap | 9651 | BLOCKED | False | True | surrun_4c7bb2d203ebf358a5a14cbc | UNDERPOWERED |
| sspec_b4b27ebccefebbfb95377bc9 | trade_date_block_bootstrap | 9652 | BLOCKED | False | True | surrun_7e34a841ed234fa0d0db1ab8 | UNDERPOWERED |
| sspec_b4b27ebccefebbfb95377bc9 | trade_date_block_bootstrap | 9653 | BLOCKED | False | True | surrun_4c6f53665f578561e55e970f | UNDERPOWERED |
| sspec_2a7e821e8cfe8e0338c4e09d | trade_date_block_bootstrap | 9654 | BLOCKED | False | True | surrun_e0fb5f25b0eda54ea5bcae6f | UNDERPOWERED |
| sspec_2a7e821e8cfe8e0338c4e09d | trade_date_block_bootstrap | 9655 | BLOCKED | False | True | surrun_e07ce642ca199411fa549ddc | UNDERPOWERED |
| sspec_2a7e821e8cfe8e0338c4e09d | trade_date_block_bootstrap | 9656 | BLOCKED | False | True | surrun_2c141fe99c842d25dd89aecb | UNDERPOWERED |
| sspec_8ad9023ec33b2254735808a2 | trade_date_block_bootstrap | 9657 | BLOCKED | False | False | surrun_21c4629207c1a15fa86e3d30 | UNDERPOWERED |
| sspec_8ad9023ec33b2254735808a2 | trade_date_block_bootstrap | 9658 | BLOCKED | False | False | surrun_c44f7d35412a9bf1cea0653b | UNDERPOWERED |
| sspec_8ad9023ec33b2254735808a2 | trade_date_block_bootstrap | 9659 | BLOCKED | False | False | surrun_77cfbe63f2556f866e04e5c3 | UNDERPOWERED |
| sspec_a70ade9e0d5fdda6b3e9feb8 | trade_date_block_bootstrap | 9660 | BLOCKED | False | True | surrun_a63bf8fb14915a7d685fb5e9 | UNDERPOWERED |
| sspec_a70ade9e0d5fdda6b3e9feb8 | trade_date_block_bootstrap | 9661 | BLOCKED | False | True | surrun_b108a9d7d4c12da1410dd7fa | UNDERPOWERED |
| sspec_a70ade9e0d5fdda6b3e9feb8 | trade_date_block_bootstrap | 9662 | BLOCKED | False | True | surrun_c35a0214c934631ae8a1b7f5 | UNDERPOWERED |
| sspec_3d223cf0b0c18bdcf28e63b6 | trade_date_block_bootstrap | 9663 | BLOCKED | False | True | surrun_49b2e74700d2128438cd86be | UNDERPOWERED |
| sspec_3d223cf0b0c18bdcf28e63b6 | trade_date_block_bootstrap | 9664 | BLOCKED | False | True | surrun_ee3e5ff57de29cb2dff09eb6 | UNDERPOWERED |
| sspec_3d223cf0b0c18bdcf28e63b6 | trade_date_block_bootstrap | 9665 | BLOCKED | False | True | surrun_ad7b8d788ba3233e4ac32245 | UNDERPOWERED |
| sspec_0e3947eeb8f43f5c9ee510ff | trade_date_block_bootstrap | 9666 | BLOCKED | False | True | surrun_099588ee194e8b9d4ab45646 | UNDERPOWERED |
| sspec_0e3947eeb8f43f5c9ee510ff | trade_date_block_bootstrap | 9667 | BLOCKED | False | True | surrun_99df015e90b757e76724da55 | UNDERPOWERED |
| sspec_0e3947eeb8f43f5c9ee510ff | trade_date_block_bootstrap | 9668 | BLOCKED | False | True | surrun_612f265f7f2e573cb1d67a7f | UNDERPOWERED |
| sspec_aa1c679817ea63ed7e62befe | trade_date_block_bootstrap | 9669 | BLOCKED | False | True | surrun_7ae3215deeb873cf7fde15c0 | UNDERPOWERED |
| sspec_aa1c679817ea63ed7e62befe | trade_date_block_bootstrap | 9670 | BLOCKED | False | True | surrun_43dbc21aa1aad5ac3be41cc2 | UNDERPOWERED |
| sspec_aa1c679817ea63ed7e62befe | trade_date_block_bootstrap | 9671 | BLOCKED | False | True | surrun_ece8d1cef633f869f6422e2c | UNDERPOWERED |
| sspec_2545d6c71d2e14cf44865f53 | trade_date_block_bootstrap | 9672 | BLOCKED | False | True | surrun_3071fb0a00c66010145e36ba | UNDERPOWERED |
| sspec_2545d6c71d2e14cf44865f53 | trade_date_block_bootstrap | 9673 | BLOCKED | False | True | surrun_4eea1b03acaebe71a479420e | UNDERPOWERED |
| sspec_2545d6c71d2e14cf44865f53 | trade_date_block_bootstrap | 9674 | BLOCKED | False | True | surrun_95d47a4eff99827d83e0ff34 | UNDERPOWERED |
| sspec_52fe4c8c50f748803ea8e053 | trade_date_block_bootstrap | 9675 | BLOCKED | False | False | surrun_42d5e702872650495f9b4d05 | UNDERPOWERED |
| sspec_52fe4c8c50f748803ea8e053 | trade_date_block_bootstrap | 9676 | BLOCKED | False | False | surrun_9031965329ecd0028fe90ed2 | UNDERPOWERED |
| sspec_52fe4c8c50f748803ea8e053 | trade_date_block_bootstrap | 9677 | BLOCKED | False | False | surrun_ad7718cd74f301d3d6788dc9 | UNDERPOWERED |
| sspec_906538aa4c237f298a69dae9 | trade_date_block_bootstrap | 9678 | BLOCKED | False | True | surrun_fcdd19bd8c167b3057c025f4 | UNDERPOWERED |
| sspec_906538aa4c237f298a69dae9 | trade_date_block_bootstrap | 9679 | BLOCKED | False | True | surrun_a200d65f9d75f413403df828 | UNDERPOWERED |
| sspec_906538aa4c237f298a69dae9 | trade_date_block_bootstrap | 9680 | BLOCKED | False | True | surrun_0e91ad08dba496ce0d2e0a1b | UNDERPOWERED |
| sspec_bd958d81b3d03af639fb80d6 | trade_date_block_bootstrap | 9681 | BLOCKED | False | True | surrun_2b21553222975cba7ed03115 | UNDERPOWERED |
| sspec_bd958d81b3d03af639fb80d6 | trade_date_block_bootstrap | 9682 | BLOCKED | False | True | surrun_42fc73bb26942b6fd064d0d7 | UNDERPOWERED |
| sspec_bd958d81b3d03af639fb80d6 | trade_date_block_bootstrap | 9683 | BLOCKED | False | True | surrun_ecbcde95e6f7cabbd3562647 | UNDERPOWERED |
| sspec_d5179015d7faddeeb88dcde2 | trade_date_block_bootstrap | 9684 | BLOCKED | False | True | surrun_1d98863b907d985497ee940e | UNDERPOWERED |
| sspec_d5179015d7faddeeb88dcde2 | trade_date_block_bootstrap | 9685 | BLOCKED | False | True | surrun_7e36168f81b8056edffe9193 | UNDERPOWERED |
| sspec_d5179015d7faddeeb88dcde2 | trade_date_block_bootstrap | 9686 | BLOCKED | False | True | surrun_158fff62cc97f3d87296a8b0 | UNDERPOWERED |
| sspec_4c52ee84f7192b03cbb0f9f4 | trade_date_block_bootstrap | 9687 | BLOCKED | False | True | surrun_9817c5d290723f38237f3067 | UNDERPOWERED |
| sspec_4c52ee84f7192b03cbb0f9f4 | trade_date_block_bootstrap | 9688 | BLOCKED | False | True | surrun_ddd43093d9517d78234430e4 | UNDERPOWERED |
| sspec_4c52ee84f7192b03cbb0f9f4 | trade_date_block_bootstrap | 9689 | BLOCKED | False | True | surrun_582bf583ab66300a3fc78daa | UNDERPOWERED |
| sspec_fc0422b844bd4f93d497f4d1 | trade_date_block_bootstrap | 9690 | BLOCKED | False | True | surrun_db5cc6926147623d8b74f423 | UNDERPOWERED |
| sspec_fc0422b844bd4f93d497f4d1 | trade_date_block_bootstrap | 9691 | BLOCKED | False | True | surrun_3c5695d6c846d44bff2d774e | UNDERPOWERED |
| sspec_fc0422b844bd4f93d497f4d1 | trade_date_block_bootstrap | 9692 | BLOCKED | False | True | surrun_7cce7f83ff16322a36623c11 | UNDERPOWERED |
| sspec_266b2582ea3bc57e083b4b1e | trade_date_block_bootstrap | 9693 | BLOCKED | False | False | surrun_ee3e3530de5f46058a5fe0a2 | UNDERPOWERED |
| sspec_266b2582ea3bc57e083b4b1e | trade_date_block_bootstrap | 9694 | BLOCKED | False | False | surrun_3a97340a2ef986c2b79a805a | UNDERPOWERED |
| sspec_266b2582ea3bc57e083b4b1e | trade_date_block_bootstrap | 9695 | BLOCKED | False | False | surrun_5f2bcaba9b631378dd58a65a | UNDERPOWERED |
| sspec_9ab1457ee56a433f4184a970 | trade_date_block_bootstrap | 9696 | BLOCKED | False | True | surrun_00307ef6a64d7d7d29a15d48 | UNDERPOWERED |
| sspec_9ab1457ee56a433f4184a970 | trade_date_block_bootstrap | 9697 | BLOCKED | False | True | surrun_488c2af35173300efbcafba3 | UNDERPOWERED |
| sspec_9ab1457ee56a433f4184a970 | trade_date_block_bootstrap | 9698 | BLOCKED | False | True | surrun_d5887eeb7414010ea702ee2a | UNDERPOWERED |
| sspec_9edfecd6f2a4082cfe787a40 | trade_date_block_bootstrap | 9699 | BLOCKED | False | True | surrun_43e4301fd712bb3ca2027eb1 | UNDERPOWERED |
| sspec_9edfecd6f2a4082cfe787a40 | trade_date_block_bootstrap | 9700 | BLOCKED | False | True | surrun_a079cb2662fc012e234c580f | UNDERPOWERED |
| sspec_9edfecd6f2a4082cfe787a40 | trade_date_block_bootstrap | 9701 | BLOCKED | False | True | surrun_6ac98c43d7c87c94917d638f | UNDERPOWERED |
| sspec_b2bd797a50aa4bfb016ce0e2 | trade_date_block_bootstrap | 9702 | BLOCKED | False | True | surrun_defb05465188782c39712ca4 | UNDERPOWERED |
| sspec_b2bd797a50aa4bfb016ce0e2 | trade_date_block_bootstrap | 9703 | BLOCKED | False | True | surrun_53c56a18387a8f75f09b02f7 | UNDERPOWERED |
| sspec_b2bd797a50aa4bfb016ce0e2 | trade_date_block_bootstrap | 9704 | BLOCKED | False | True | surrun_a44e46a0d707c676bdf1e7c1 | UNDERPOWERED |
| sspec_6d77b448d271da92905c259f | trade_date_block_bootstrap | 9705 | BLOCKED | False | True | surrun_c76c3840d34394f75bbbadd8 | UNDERPOWERED |
| sspec_6d77b448d271da92905c259f | trade_date_block_bootstrap | 9706 | BLOCKED | False | True | surrun_f91ea9f63912a7566e34abe3 | UNDERPOWERED |
| sspec_6d77b448d271da92905c259f | trade_date_block_bootstrap | 9707 | BLOCKED | False | True | surrun_66447e781faefa2ede251c91 | UNDERPOWERED |
| sspec_56b36be15fe92226fdc753d0 | trade_date_block_bootstrap | 9708 | BLOCKED | False | True | surrun_d9b0599ffb59c56727b4582b | UNDERPOWERED |
| sspec_56b36be15fe92226fdc753d0 | trade_date_block_bootstrap | 9709 | BLOCKED | False | True | surrun_58a9adf7e59902a8cd587e1f | UNDERPOWERED |
| sspec_56b36be15fe92226fdc753d0 | trade_date_block_bootstrap | 9710 | BLOCKED | False | True | surrun_40336854802107d4876aed16 | UNDERPOWERED |
| sspec_dbd6f3316ed1bef876603a0b | trade_date_block_bootstrap | 9711 | BLOCKED | False | False | surrun_4907c58ac948dd16d2dee648 | UNDERPOWERED |
| sspec_dbd6f3316ed1bef876603a0b | trade_date_block_bootstrap | 9712 | BLOCKED | False | False | surrun_ab95fad50ecd12e98adfb9fd | UNDERPOWERED |
| sspec_dbd6f3316ed1bef876603a0b | trade_date_block_bootstrap | 9713 | BLOCKED | False | False | surrun_a58a9d95afbd38b027adb2da | UNDERPOWERED |
| sspec_ee08e420765f3ac974b34592 | trade_date_block_bootstrap | 9714 | BLOCKED | False | True | surrun_89b5675f2a9c94952ea4cfa3 | UNDERPOWERED |
| sspec_ee08e420765f3ac974b34592 | trade_date_block_bootstrap | 9715 | BLOCKED | False | True | surrun_e0b5723fee2975283c04a025 | UNDERPOWERED |
| sspec_ee08e420765f3ac974b34592 | trade_date_block_bootstrap | 9716 | BLOCKED | False | True | surrun_6da8f4158b0b12ab02603799 | UNDERPOWERED |
| sspec_38fd9e95dced1b5c59555f8e | trade_date_block_bootstrap | 9717 | BLOCKED | False | True | surrun_2efc7254600645185085b44f | UNDERPOWERED |
| sspec_38fd9e95dced1b5c59555f8e | trade_date_block_bootstrap | 9718 | BLOCKED | False | True | surrun_68254ccfa43697a0ceba93b8 | UNDERPOWERED |
| sspec_38fd9e95dced1b5c59555f8e | trade_date_block_bootstrap | 9719 | BLOCKED | False | True | surrun_156e9f1d2feb1973f67ae18f | UNDERPOWERED |
| sspec_bcf919f46741213c2f4a1c49 | trade_date_block_bootstrap | 9720 | BLOCKED | False | True | surrun_d4206071aa0e006b77d7b263 | UNDERPOWERED |
| sspec_bcf919f46741213c2f4a1c49 | trade_date_block_bootstrap | 9721 | BLOCKED | False | True | surrun_495fea6f187ac235b1f2af8e | UNDERPOWERED |
| sspec_bcf919f46741213c2f4a1c49 | trade_date_block_bootstrap | 9722 | BLOCKED | False | True | surrun_2fc3ae29361d34e3ce6b54c0 | UNDERPOWERED |
| sspec_daa74863126dc5d1d2fe9b65 | trade_date_block_bootstrap | 9723 | BLOCKED | False | True | surrun_102d19afc6c14b8c82f47f50 | UNDERPOWERED |
| sspec_daa74863126dc5d1d2fe9b65 | trade_date_block_bootstrap | 9724 | BLOCKED | False | True | surrun_c12fba1883aa25314c6a4374 | UNDERPOWERED |
| sspec_daa74863126dc5d1d2fe9b65 | trade_date_block_bootstrap | 9725 | BLOCKED | False | True | surrun_b6d06ab698155044c2139e5b | UNDERPOWERED |
| sspec_cf05e6c5ca7e43d6050aa3fc | trade_date_block_bootstrap | 9726 | BLOCKED | False | True | surrun_49bcef61f9dd286fe38bd93e | UNDERPOWERED |
| sspec_cf05e6c5ca7e43d6050aa3fc | trade_date_block_bootstrap | 9727 | BLOCKED | False | True | surrun_d1f822fddf667d9c3ff14dca | UNDERPOWERED |
| sspec_cf05e6c5ca7e43d6050aa3fc | trade_date_block_bootstrap | 9728 | BLOCKED | False | True | surrun_37feeaafe755827cf0f11ebf | UNDERPOWERED |
| sspec_e8fe071c662ff3bf070405f8 | trade_date_block_bootstrap | 9729 | BLOCKED | False | False | surrun_c78afcffd0b855956ddf2b49 | UNDERPOWERED |
| sspec_e8fe071c662ff3bf070405f8 | trade_date_block_bootstrap | 9730 | BLOCKED | False | False | surrun_abddb51b6c34b738c0b519a0 | UNDERPOWERED |
| sspec_e8fe071c662ff3bf070405f8 | trade_date_block_bootstrap | 9731 | BLOCKED | False | False | surrun_05be336ccf8f23834a6946c7 | UNDERPOWERED |
| sspec_04a2df8739a0cc17b48da8fe | trade_date_block_bootstrap | 9732 | BLOCKED | False | True | surrun_73dae70c968b2c5cf4ab20af | UNDERPOWERED |
| sspec_04a2df8739a0cc17b48da8fe | trade_date_block_bootstrap | 9733 | BLOCKED | False | True | surrun_82c8bcfdb04646810027541c | UNDERPOWERED |
| sspec_04a2df8739a0cc17b48da8fe | trade_date_block_bootstrap | 9734 | BLOCKED | False | True | surrun_6de13dcd561464fd60de5da9 | UNDERPOWERED |
| sspec_127c129af9d05112fc66ba6a | trade_date_block_bootstrap | 9735 | BLOCKED | False | True | surrun_059500dde7ef905362b14d9d | UNDERPOWERED |
| sspec_127c129af9d05112fc66ba6a | trade_date_block_bootstrap | 9736 | BLOCKED | False | True | surrun_ffd70abd7ceb25ee180849fb | UNDERPOWERED |
| sspec_127c129af9d05112fc66ba6a | trade_date_block_bootstrap | 9737 | BLOCKED | False | True | surrun_70b3ffc477ada87e8ca89dd0 | UNDERPOWERED |
| sspec_f91da9fd1dee2cf6ab22a683 | trade_date_block_bootstrap | 9738 | BLOCKED | False | True | surrun_db607eff5f43028031a7bbdf | UNDERPOWERED |
| sspec_f91da9fd1dee2cf6ab22a683 | trade_date_block_bootstrap | 9739 | BLOCKED | False | True | surrun_6031a6e08e2ad02cf8bacf04 | UNDERPOWERED |
| sspec_f91da9fd1dee2cf6ab22a683 | trade_date_block_bootstrap | 9740 | BLOCKED | False | True | surrun_b3e23acd29160daca9519764 | UNDERPOWERED |
| sspec_8d138227ba78ba8cbf39e911 | trade_date_block_bootstrap | 9741 | BLOCKED | False | True | surrun_fb2f845d167dce8f168cc1d9 | UNDERPOWERED |
| sspec_8d138227ba78ba8cbf39e911 | trade_date_block_bootstrap | 9742 | BLOCKED | False | True | surrun_8e7d042bd17f51cb4ba01b75 | UNDERPOWERED |
| sspec_8d138227ba78ba8cbf39e911 | trade_date_block_bootstrap | 9743 | BLOCKED | False | True | surrun_8323b55a559144b3785e11e5 | UNDERPOWERED |
| sspec_8e77d8eec760215ec7ab820e | trade_date_block_bootstrap | 9744 | BLOCKED | False | True | surrun_f544360d0e3eceba1e0409df | UNDERPOWERED |
| sspec_8e77d8eec760215ec7ab820e | trade_date_block_bootstrap | 9745 | BLOCKED | False | True | surrun_4c97683b6664a9adcff9804f | UNDERPOWERED |
| sspec_8e77d8eec760215ec7ab820e | trade_date_block_bootstrap | 9746 | BLOCKED | False | True | surrun_a5686967a1018b39a6065412 | UNDERPOWERED |
| sspec_ac9d363d2b436f470e8d8ee3 | trade_date_block_bootstrap | 9747 | BLOCKED | False | False | surrun_6869b913563b55a7e1a73212 | UNDERPOWERED |
| sspec_ac9d363d2b436f470e8d8ee3 | trade_date_block_bootstrap | 9748 | BLOCKED | False | False | surrun_6b8d380d6fdc12a00822578f | UNDERPOWERED |
| sspec_ac9d363d2b436f470e8d8ee3 | trade_date_block_bootstrap | 9749 | BLOCKED | False | False | surrun_3a365104cd064b3c5d0cd692 | UNDERPOWERED |
| sspec_6f5f81332c4b9e51a077ab12 | trade_date_block_bootstrap | 9750 | BLOCKED | False | True | surrun_ce3193bbfd4d6233e29944d1 | UNDERPOWERED |
| sspec_6f5f81332c4b9e51a077ab12 | trade_date_block_bootstrap | 9751 | BLOCKED | False | True | surrun_02cfe7e847271fb6b5881569 | UNDERPOWERED |
| sspec_6f5f81332c4b9e51a077ab12 | trade_date_block_bootstrap | 9752 | BLOCKED | False | True | surrun_236dd986f059d57d472b20f0 | UNDERPOWERED |
| sspec_939b09c440e48b973655ac7a | trade_date_block_bootstrap | 9753 | BLOCKED | False | True | surrun_abe2438d1398f0c241b956b5 | UNDERPOWERED |
| sspec_939b09c440e48b973655ac7a | trade_date_block_bootstrap | 9754 | BLOCKED | False | True | surrun_de797c6cc756a909c7e11d8b | UNDERPOWERED |
| sspec_939b09c440e48b973655ac7a | trade_date_block_bootstrap | 9755 | BLOCKED | False | True | surrun_7a0fbf4e941a8d826aa47331 | UNDERPOWERED |
| sspec_6f3194d08eeca0085661f8b4 | trade_date_block_bootstrap | 9756 | BLOCKED | False | True | surrun_9d043f8dc89b780764ad34eb | UNDERPOWERED |
| sspec_6f3194d08eeca0085661f8b4 | trade_date_block_bootstrap | 9757 | BLOCKED | False | True | surrun_006751554b5e13e234b65916 | UNDERPOWERED |
| sspec_6f3194d08eeca0085661f8b4 | trade_date_block_bootstrap | 9758 | BLOCKED | False | True | surrun_026c13bd149dd0060ced0a90 | UNDERPOWERED |
| sspec_5fb65a4b05a75b3caa99d2de | trade_date_block_bootstrap | 9759 | BLOCKED | False | True | surrun_7dfdfa18f25141403f34e6cd | UNDERPOWERED |
| sspec_5fb65a4b05a75b3caa99d2de | trade_date_block_bootstrap | 9760 | BLOCKED | False | True | surrun_ab5f2ea92614057a7b3f2e4a | UNDERPOWERED |
| sspec_5fb65a4b05a75b3caa99d2de | trade_date_block_bootstrap | 9761 | BLOCKED | False | True | surrun_c3f7f2657363848ec0f251fe | UNDERPOWERED |
| sspec_082ddde49070511dbd490d9b | trade_date_block_bootstrap | 9762 | BLOCKED | False | True | surrun_fcde445150de12bd2f96649d | UNDERPOWERED |
| sspec_082ddde49070511dbd490d9b | trade_date_block_bootstrap | 9763 | BLOCKED | False | True | surrun_69ceaecbaad2b15011699909 | UNDERPOWERED |
| sspec_082ddde49070511dbd490d9b | trade_date_block_bootstrap | 9764 | BLOCKED | False | True | surrun_d80035302fba111a1bf5f594 | UNDERPOWERED |
| sspec_de80c2b2edc917743028d32c | trade_date_block_bootstrap | 9765 | BLOCKED | False | False | surrun_ae08411cf873f2e054befa50 | UNDERPOWERED |
| sspec_de80c2b2edc917743028d32c | trade_date_block_bootstrap | 9766 | BLOCKED | False | False | surrun_1d459afb826bbd34190aa205 | UNDERPOWERED |
| sspec_de80c2b2edc917743028d32c | trade_date_block_bootstrap | 9767 | BLOCKED | False | False | surrun_68ae67ee2fa72719cc9c04c9 | UNDERPOWERED |
| sspec_a75cb3c454f8767e94ddee80 | trade_date_block_bootstrap | 9768 | BLOCKED | False | True | surrun_9ed532dec8528ff432691a73 | UNDERPOWERED |
| sspec_a75cb3c454f8767e94ddee80 | trade_date_block_bootstrap | 9769 | BLOCKED | False | True | surrun_8b932f7768c68da8a73fce28 | UNDERPOWERED |
| sspec_a75cb3c454f8767e94ddee80 | trade_date_block_bootstrap | 9770 | BLOCKED | False | True | surrun_20adaf1d967fcb0686426c6e | UNDERPOWERED |
| sspec_1057a08e3cc08ecfdafe6f48 | trade_date_block_bootstrap | 9771 | BLOCKED | False | True | surrun_5c1b695ea70d41a8bdffae79 | UNDERPOWERED |
| sspec_1057a08e3cc08ecfdafe6f48 | trade_date_block_bootstrap | 9772 | BLOCKED | False | True | surrun_9fffd946f69675ef73f00858 | UNDERPOWERED |
| sspec_1057a08e3cc08ecfdafe6f48 | trade_date_block_bootstrap | 9773 | BLOCKED | False | True | surrun_db80227dff12b174f44ea3fb | UNDERPOWERED |
| sspec_940856ef6edb85218ad49390 | trade_date_block_bootstrap | 9774 | BLOCKED | False | True | surrun_fe176b98621b3b9634d4e912 | UNDERPOWERED |
| sspec_940856ef6edb85218ad49390 | trade_date_block_bootstrap | 9775 | BLOCKED | False | True | surrun_c3f3b52f165dbb26d2e330e5 | UNDERPOWERED |
| sspec_940856ef6edb85218ad49390 | trade_date_block_bootstrap | 9776 | BLOCKED | False | True | surrun_fed877e92d9968803527d74f | UNDERPOWERED |
| sspec_161989af873a975826c319c4 | trade_date_block_bootstrap | 9777 | BLOCKED | False | True | surrun_764fb833295d1b91aa41bd5b | UNDERPOWERED |
| sspec_161989af873a975826c319c4 | trade_date_block_bootstrap | 9778 | BLOCKED | False | True | surrun_4d4440f542f37506a3c8180e | UNDERPOWERED |
| sspec_161989af873a975826c319c4 | trade_date_block_bootstrap | 9779 | BLOCKED | False | True | surrun_1ae60bf13d2ddee26fb6e031 | UNDERPOWERED |
| sspec_bbeb958477a1fc89451ddeab | trade_date_block_bootstrap | 9780 | BLOCKED | False | True | surrun_fde2b988ce90440cfc1b6f68 | UNDERPOWERED |
| sspec_bbeb958477a1fc89451ddeab | trade_date_block_bootstrap | 9781 | BLOCKED | False | True | surrun_9a37aab4826dbbfed1973f25 | UNDERPOWERED |
| sspec_bbeb958477a1fc89451ddeab | trade_date_block_bootstrap | 9782 | BLOCKED | False | True | surrun_bae27b7df12d5e15e89f9ce4 | UNDERPOWERED |
| sspec_87fc86a4547aa5303033e553 | trade_date_block_bootstrap | 9783 | BLOCKED | False | False | surrun_a65b95c94a92327d569f3823 | UNDERPOWERED |
| sspec_87fc86a4547aa5303033e553 | trade_date_block_bootstrap | 9784 | BLOCKED | False | False | surrun_3923012f0647dd3ab264aa5f | UNDERPOWERED |
| sspec_87fc86a4547aa5303033e553 | trade_date_block_bootstrap | 9785 | BLOCKED | False | False | surrun_5a8b8f93583593d5b7a5c6d1 | UNDERPOWERED |
| sspec_275870335e86592600d51850 | trade_date_block_bootstrap | 9786 | BLOCKED | False | True | surrun_a79e82b73da4312a27c881ae | UNDERPOWERED |
| sspec_275870335e86592600d51850 | trade_date_block_bootstrap | 9787 | BLOCKED | False | True | surrun_e97352b6add221e991c23224 | UNDERPOWERED |
| sspec_275870335e86592600d51850 | trade_date_block_bootstrap | 9788 | BLOCKED | False | True | surrun_7208f0b966e3b85ee483db2e | UNDERPOWERED |
| sspec_86a27d94f4e7006b8c4676a0 | trade_date_block_bootstrap | 9789 | BLOCKED | False | True | surrun_3d793cda4b996ee83092f6ce | UNDERPOWERED |
| sspec_86a27d94f4e7006b8c4676a0 | trade_date_block_bootstrap | 9790 | BLOCKED | False | True | surrun_4367c7f0b0b1e9233f005124 | UNDERPOWERED |
| sspec_86a27d94f4e7006b8c4676a0 | trade_date_block_bootstrap | 9791 | BLOCKED | False | True | surrun_46391bca4d91e4f511c6b818 | UNDERPOWERED |
| sspec_47eb77fbcd4bd6fd9a52ef54 | trade_date_block_bootstrap | 9792 | BLOCKED | False | True | surrun_72e256046b513c15d30b8941 | UNDERPOWERED |
| sspec_47eb77fbcd4bd6fd9a52ef54 | trade_date_block_bootstrap | 9793 | BLOCKED | False | True | surrun_8455b3947c4792878bbdd608 | UNDERPOWERED |
| sspec_47eb77fbcd4bd6fd9a52ef54 | trade_date_block_bootstrap | 9794 | BLOCKED | False | True | surrun_cdb778c15d80ea1c9d1dfe16 | UNDERPOWERED |
| sspec_d6693d28401596a59eb97669 | trade_date_block_bootstrap | 9795 | BLOCKED | False | True | surrun_0fa39fe64e2c59ef0e4922f4 | UNDERPOWERED |
| sspec_d6693d28401596a59eb97669 | trade_date_block_bootstrap | 9796 | BLOCKED | False | True | surrun_cf0ee235211b8c415d8f3cef | UNDERPOWERED |
| sspec_d6693d28401596a59eb97669 | trade_date_block_bootstrap | 9797 | BLOCKED | False | True | surrun_99945fcbad97da886c29d3e9 | UNDERPOWERED |
| sspec_086c78ab31b02489b4731d14 | trade_date_block_bootstrap | 9798 | BLOCKED | False | True | surrun_e595ef28b76f52013c2c00bf | UNDERPOWERED |
| sspec_086c78ab31b02489b4731d14 | trade_date_block_bootstrap | 9799 | BLOCKED | False | True | surrun_7345fa17cd3b9387b49a9e49 | UNDERPOWERED |
| sspec_086c78ab31b02489b4731d14 | trade_date_block_bootstrap | 9800 | BLOCKED | False | True | surrun_b706230c726ce79800981e5e | UNDERPOWERED |
| sspec_1c1c862cb092207bfd9b5cf1 | trade_date_block_bootstrap | 9801 | BLOCKED | False | False | surrun_97bc2bd0e15ed0fa9764a8a7 | UNDERPOWERED |
| sspec_1c1c862cb092207bfd9b5cf1 | trade_date_block_bootstrap | 9802 | BLOCKED | False | False | surrun_3050d1d13b9de7c4c26e4ba3 | UNDERPOWERED |
| sspec_1c1c862cb092207bfd9b5cf1 | trade_date_block_bootstrap | 9803 | BLOCKED | False | False | surrun_ddeb13e4723870280905c942 | UNDERPOWERED |
| sspec_311a86fec1da6be4845d0cd1 | trade_date_block_bootstrap | 9804 | BLOCKED | False | True | surrun_20d60152c5c9ec8f94f29833 | UNDERPOWERED |
| sspec_311a86fec1da6be4845d0cd1 | trade_date_block_bootstrap | 9805 | BLOCKED | False | True | surrun_8d333b2c0eefaa096e9b9d53 | UNDERPOWERED |
| sspec_311a86fec1da6be4845d0cd1 | trade_date_block_bootstrap | 9806 | BLOCKED | False | True | surrun_8d961c0a0dce19d111a1d2cf | UNDERPOWERED |
| sspec_d732889738c6e30af89f8979 | trade_date_block_bootstrap | 9807 | BLOCKED | False | True | surrun_0b06d8d52026576b0c3d2a8b | UNDERPOWERED |
| sspec_d732889738c6e30af89f8979 | trade_date_block_bootstrap | 9808 | BLOCKED | False | True | surrun_d6763d51a76b0cfb63f15792 | UNDERPOWERED |
| sspec_d732889738c6e30af89f8979 | trade_date_block_bootstrap | 9809 | BLOCKED | False | True | surrun_6cdea13b1c7ec9be3dd53a4e | UNDERPOWERED |
| sspec_a357b1e5e03870e2a92b4670 | trade_date_block_bootstrap | 9810 | BLOCKED | False | True | surrun_6005b6d30db80269eae36fe8 | UNDERPOWERED |
| sspec_a357b1e5e03870e2a92b4670 | trade_date_block_bootstrap | 9811 | BLOCKED | False | True | surrun_921d464b49f38978b0e05956 | UNDERPOWERED |
| sspec_a357b1e5e03870e2a92b4670 | trade_date_block_bootstrap | 9812 | BLOCKED | False | True | surrun_a61bb5d6a33c458ddb9fb2ec | UNDERPOWERED |
| sspec_13fc592d52ed884202b5cff0 | trade_date_block_bootstrap | 9813 | BLOCKED | False | True | surrun_3e0898a5f75e67a3fb35ee9c | UNDERPOWERED |
| sspec_13fc592d52ed884202b5cff0 | trade_date_block_bootstrap | 9814 | BLOCKED | False | True | surrun_a205a3621564349ac1def45e | UNDERPOWERED |
| sspec_13fc592d52ed884202b5cff0 | trade_date_block_bootstrap | 9815 | BLOCKED | False | True | surrun_2610908f96276e7a265f0c29 | UNDERPOWERED |
| sspec_052a79991cf1b05d4a9a1de1 | trade_date_block_bootstrap | 9816 | BLOCKED | False | True | surrun_eb13e43e0e559b804c154841 | UNDERPOWERED |
| sspec_052a79991cf1b05d4a9a1de1 | trade_date_block_bootstrap | 9817 | BLOCKED | False | True | surrun_4d5c4078aa73495602f36050 | UNDERPOWERED |
| sspec_052a79991cf1b05d4a9a1de1 | trade_date_block_bootstrap | 9818 | BLOCKED | False | True | surrun_d03189c8bfb629d20deecc71 | UNDERPOWERED |
| sspec_8165de75ec50096ec9ee007c | trade_date_block_bootstrap | 9819 | BLOCKED | False | False | surrun_42e2ec6dc57301c8f664fc45 | UNDERPOWERED |
| sspec_8165de75ec50096ec9ee007c | trade_date_block_bootstrap | 9820 | BLOCKED | False | False | surrun_e8973d9ac02f5bdcae24ca0a | UNDERPOWERED |
| sspec_8165de75ec50096ec9ee007c | trade_date_block_bootstrap | 9821 | BLOCKED | False | False | surrun_ba489fa175c5c7a315a49589 | UNDERPOWERED |
| sspec_42c51db6a9e7b71fb4c73838 | trade_date_block_bootstrap | 9822 | BLOCKED | False | True | surrun_2805f0fa8bf18c8aeb02a49c | UNDERPOWERED |
| sspec_42c51db6a9e7b71fb4c73838 | trade_date_block_bootstrap | 9823 | BLOCKED | False | True | surrun_5123801edc2c826396a0339b | UNDERPOWERED |
| sspec_42c51db6a9e7b71fb4c73838 | trade_date_block_bootstrap | 9824 | BLOCKED | False | True | surrun_a3685fef8b77fa5bcbce9470 | UNDERPOWERED |
| sspec_1103980d45370aae6701e349 | trade_date_block_bootstrap | 9825 | BLOCKED | False | True | surrun_c86ff8f01757868a5b7e4af7 | UNDERPOWERED |
| sspec_1103980d45370aae6701e349 | trade_date_block_bootstrap | 9826 | BLOCKED | False | True | surrun_df42e822e3424dc7e04b115b | UNDERPOWERED |
| sspec_1103980d45370aae6701e349 | trade_date_block_bootstrap | 9827 | BLOCKED | False | True | surrun_9fe5199420b41f12bf9be598 | UNDERPOWERED |
| sspec_296aa7135559fd36871c9013 | trade_date_block_bootstrap | 9828 | BLOCKED | False | True | surrun_032a72ca39daf439f4966aaa | UNDERPOWERED |
| sspec_296aa7135559fd36871c9013 | trade_date_block_bootstrap | 9829 | BLOCKED | False | True | surrun_ead0942596df5896aa157d73 | UNDERPOWERED |
| sspec_296aa7135559fd36871c9013 | trade_date_block_bootstrap | 9830 | BLOCKED | False | True | surrun_0764f5d51d7aa103e23df3bb | UNDERPOWERED |
| sspec_a3efbe6cf9248d8af1a6c860 | trade_date_block_bootstrap | 9831 | BLOCKED | False | True | surrun_d8c072f767c6dad3cbc94543 | UNDERPOWERED |
| sspec_a3efbe6cf9248d8af1a6c860 | trade_date_block_bootstrap | 9832 | BLOCKED | False | True | surrun_243eefd4c1ec6e57a861ee0e | UNDERPOWERED |
| sspec_a3efbe6cf9248d8af1a6c860 | trade_date_block_bootstrap | 9833 | BLOCKED | False | True | surrun_64f9269497017f42356ea533 | UNDERPOWERED |
| sspec_60230ee600937f837eb9ac8b | trade_date_block_bootstrap | 9834 | BLOCKED | False | True | surrun_4476fc0cf32dfeaf3799ac25 | UNDERPOWERED |
| sspec_60230ee600937f837eb9ac8b | trade_date_block_bootstrap | 9835 | BLOCKED | False | True | surrun_65535257c41fe4bdfaae230d | UNDERPOWERED |
| sspec_60230ee600937f837eb9ac8b | trade_date_block_bootstrap | 9836 | BLOCKED | False | True | surrun_8615c8c13e94decb95898c31 | UNDERPOWERED |
| sspec_6d52f8c3bd36c0a81fd89009 | trade_date_block_bootstrap | 9837 | BLOCKED | False | False | surrun_afe764efc7c4b151b8616952 | UNDERPOWERED |
| sspec_6d52f8c3bd36c0a81fd89009 | trade_date_block_bootstrap | 9838 | BLOCKED | False | False | surrun_b1958db7aeb096ed49b9a1d9 | UNDERPOWERED |
| sspec_6d52f8c3bd36c0a81fd89009 | trade_date_block_bootstrap | 9839 | BLOCKED | False | False | surrun_92e9bf13ccbb35df986bee9b | UNDERPOWERED |
| sspec_c280d702605e8d161fdcba9a | trade_date_block_bootstrap | 9840 | BLOCKED | False | True | surrun_9b76737bf92643a4413e6d6a | UNDERPOWERED |
| sspec_c280d702605e8d161fdcba9a | trade_date_block_bootstrap | 9841 | BLOCKED | False | True | surrun_68dce7f9523e997729e3c179 | UNDERPOWERED |
| sspec_c280d702605e8d161fdcba9a | trade_date_block_bootstrap | 9842 | BLOCKED | False | True | surrun_2025231c2c7eae6763635a32 | UNDERPOWERED |
| sspec_04a8d81bbfd7998662d85571 | trade_date_block_bootstrap | 9843 | BLOCKED | False | True | surrun_3e12f96e636b2d65d94a264c | UNDERPOWERED |
| sspec_04a8d81bbfd7998662d85571 | trade_date_block_bootstrap | 9844 | BLOCKED | False | True | surrun_40ba058f45e4b2b41ebc474d | UNDERPOWERED |
| sspec_04a8d81bbfd7998662d85571 | trade_date_block_bootstrap | 9845 | BLOCKED | False | True | surrun_fc4115b37d79e7a27ff8b9e3 | UNDERPOWERED |
| sspec_69f78a1a7473a04f57aee125 | trade_date_block_bootstrap | 9846 | BLOCKED | False | True | surrun_6d74b8d20a81fec9dbad24f9 | UNDERPOWERED |
| sspec_69f78a1a7473a04f57aee125 | trade_date_block_bootstrap | 9847 | BLOCKED | False | True | surrun_6c9bd9759fd510345ae435ad | UNDERPOWERED |
| sspec_69f78a1a7473a04f57aee125 | trade_date_block_bootstrap | 9848 | BLOCKED | False | True | surrun_bc48d10e32bd572400f3e738 | UNDERPOWERED |
| sspec_a2c9760321679f58a980bfad | trade_date_block_bootstrap | 9849 | BLOCKED | False | True | surrun_fa26d95c34b7c431ae80ebdf | UNDERPOWERED |
| sspec_a2c9760321679f58a980bfad | trade_date_block_bootstrap | 9850 | BLOCKED | False | True | surrun_c2ec6ab7e9f30635c6ca3b1a | UNDERPOWERED |
| sspec_a2c9760321679f58a980bfad | trade_date_block_bootstrap | 9851 | BLOCKED | False | True | surrun_305ef0d91b5c55372e51bc55 | UNDERPOWERED |
| sspec_7546239329995db0827623eb | trade_date_block_bootstrap | 9852 | BLOCKED | False | True | surrun_2b3181978313b3fc8e27b9ef | UNDERPOWERED |
| sspec_7546239329995db0827623eb | trade_date_block_bootstrap | 9853 | BLOCKED | False | True | surrun_60136365125b46ce08fc5ddd | UNDERPOWERED |
| sspec_7546239329995db0827623eb | trade_date_block_bootstrap | 9854 | BLOCKED | False | True | surrun_32555fff48a7b541fec8197c | UNDERPOWERED |
| sspec_d8be1146f7466118c077d809 | trade_date_block_bootstrap | 9855 | BLOCKED | False | False | surrun_5c7c8dfdbef950ce507cfd61 | UNDERPOWERED |
| sspec_d8be1146f7466118c077d809 | trade_date_block_bootstrap | 9856 | BLOCKED | False | False | surrun_90c3021b23401f33884ee70a | UNDERPOWERED |
| sspec_d8be1146f7466118c077d809 | trade_date_block_bootstrap | 9857 | BLOCKED | False | False | surrun_46a06f7953f1a9ce60ab785b | UNDERPOWERED |
| sspec_539236624ffa674c3bb4e40d | trade_date_block_bootstrap | 9858 | BLOCKED | False | True | surrun_59d45fb28757ad373b4ebd87 | UNDERPOWERED |
| sspec_539236624ffa674c3bb4e40d | trade_date_block_bootstrap | 9859 | BLOCKED | False | True | surrun_357ab01914d2f9c4e8d97ad2 | UNDERPOWERED |
| sspec_539236624ffa674c3bb4e40d | trade_date_block_bootstrap | 9860 | BLOCKED | False | True | surrun_f75529e8fada60f0f2d33105 | UNDERPOWERED |
| sspec_118fd64cad94c8a9151f1f48 | trade_date_block_bootstrap | 9861 | BLOCKED | False | True | surrun_d8a2601eea6c36a49444034a | UNDERPOWERED |
| sspec_118fd64cad94c8a9151f1f48 | trade_date_block_bootstrap | 9862 | BLOCKED | False | True | surrun_da166033ae42f7bbc785efe3 | UNDERPOWERED |
| sspec_118fd64cad94c8a9151f1f48 | trade_date_block_bootstrap | 9863 | BLOCKED | False | True | surrun_16d87f6e44927243e7152553 | UNDERPOWERED |

## Machinery Inventory

- `SurrogateStudyRun` schema and deterministic serialization live in `src/alpha_system/governance/surrogate_run.py`.
- `surrogate_flag` is threaded through `TrialLedgerRecord`; true surrogate trials are excluded from production variant/family counts.
- `alpha governance surrogate-calibrate` runs seeded surrogate calibrations in caller-supplied isolated namespaces.
- Real-data calibration over the kill-shot StudySpec remains a coordinator runbook step before FUTSUB-P28 kill-shot resume.
