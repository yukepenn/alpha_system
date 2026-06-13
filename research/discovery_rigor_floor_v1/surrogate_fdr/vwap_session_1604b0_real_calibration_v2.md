# Real-Data Surrogate Calibration: sspec_1604b063f3a3401208ee0239

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
- Isolated namespace: `/home/yuke_zhang/alpha_data/alpha_system/rigor_p05_surrogate_v5_vwap_1604b0`.

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
| sspec_00145d6a03aacd0a55a51408 | trade_date_block_shuffle | 9300 | BLOCKED | False | True | surrun_ca55cc9b75975bf0420b4485 | UNDERPOWERED |
| sspec_00145d6a03aacd0a55a51408 | trade_date_block_shuffle | 9301 | BLOCKED | False | True | surrun_42fbeffb14756ae6d2a1ac5b | UNDERPOWERED |
| sspec_00145d6a03aacd0a55a51408 | trade_date_block_shuffle | 9302 | BLOCKED | False | True | surrun_2181f3f1c73bd06061814077 | UNDERPOWERED |
| sspec_e0e747934316205e581e3230 | trade_date_block_shuffle | 9303 | BLOCKED | False | True | surrun_3df0bf3baeabaa7c1458c2c1 | UNDERPOWERED |
| sspec_e0e747934316205e581e3230 | trade_date_block_shuffle | 9304 | BLOCKED | False | True | surrun_1a0bbb7792421ebdc16c0741 | UNDERPOWERED |
| sspec_e0e747934316205e581e3230 | trade_date_block_shuffle | 9305 | BLOCKED | False | True | surrun_6b5c5462ca6a6561f4cdd17a | UNDERPOWERED |
| sspec_5b5f138648471fb016566a96 | trade_date_block_shuffle | 9306 | BLOCKED | False | True | surrun_aa46d0fd9c6ba03f8047163a | UNDERPOWERED |
| sspec_5b5f138648471fb016566a96 | trade_date_block_shuffle | 9307 | BLOCKED | False | True | surrun_3e4089f8024e3559f6d97f67 | UNDERPOWERED |
| sspec_5b5f138648471fb016566a96 | trade_date_block_shuffle | 9308 | BLOCKED | False | True | surrun_806ef45124d4ab11b57c47f0 | UNDERPOWERED |
| sspec_641962ccd20eafc96802967f | trade_date_block_shuffle | 9309 | BLOCKED | False | False | surrun_b5338b4537df8d2669a9db93 | UNDERPOWERED |
| sspec_641962ccd20eafc96802967f | trade_date_block_shuffle | 9310 | BLOCKED | False | False | surrun_c7c3f4d3fbb23309abac48b4 | UNDERPOWERED |
| sspec_641962ccd20eafc96802967f | trade_date_block_shuffle | 9311 | BLOCKED | False | False | surrun_9b9b066ae5d8dc8a6d2c44ca | UNDERPOWERED |
| sspec_130a69ed17c50e2ea8e1550b | trade_date_block_shuffle | 9312 | BLOCKED | False | True | surrun_cdc14e430d758a62926c594e | UNDERPOWERED |
| sspec_130a69ed17c50e2ea8e1550b | trade_date_block_shuffle | 9313 | BLOCKED | False | True | surrun_66cd01228bc45683e5e429da | UNDERPOWERED |
| sspec_130a69ed17c50e2ea8e1550b | trade_date_block_shuffle | 9314 | BLOCKED | False | True | surrun_0f2f272d66c6994a138cdf32 | UNDERPOWERED |
| sspec_005843739d7960855d199691 | trade_date_block_shuffle | 9315 | BLOCKED | False | True | surrun_13a13aa85ce53a3fc7d2c3e6 | UNDERPOWERED |
| sspec_005843739d7960855d199691 | trade_date_block_shuffle | 9316 | BLOCKED | False | True | surrun_fc1f34260568710fd9b426df | UNDERPOWERED |
| sspec_005843739d7960855d199691 | trade_date_block_shuffle | 9317 | BLOCKED | False | True | surrun_649c2f3121c30a6d46f5c5ea | UNDERPOWERED |
| sspec_1d2ea6eeab7c66800c18eb3c | trade_date_block_shuffle | 9318 | BLOCKED | False | True | surrun_ad37d330dd17d31d0dec7701 | UNDERPOWERED |
| sspec_1d2ea6eeab7c66800c18eb3c | trade_date_block_shuffle | 9319 | BLOCKED | False | True | surrun_12c6c7687d6873431d3b5d50 | UNDERPOWERED |
| sspec_1d2ea6eeab7c66800c18eb3c | trade_date_block_shuffle | 9320 | BLOCKED | False | True | surrun_4ae685b3edd7cdd9a3aef9c4 | UNDERPOWERED |
| sspec_7447452da67d19f4bdabe883 | trade_date_block_shuffle | 9321 | BLOCKED | False | True | surrun_983c59bf8e3c4f3c3baaf10c | UNDERPOWERED |
| sspec_7447452da67d19f4bdabe883 | trade_date_block_shuffle | 9322 | BLOCKED | False | True | surrun_6e9ab3c3c329c075794a990a | UNDERPOWERED |
| sspec_7447452da67d19f4bdabe883 | trade_date_block_shuffle | 9323 | BLOCKED | False | True | surrun_0ee3dbee4e237ad749e75e73 | UNDERPOWERED |
| sspec_f7ced723232cbac818ab4c9f | trade_date_block_shuffle | 9324 | BLOCKED | False | True | surrun_6e831d6fe8519f7b71722cf9 | UNDERPOWERED |
| sspec_f7ced723232cbac818ab4c9f | trade_date_block_shuffle | 9325 | BLOCKED | False | True | surrun_454aaa5466e1a686e9fed1ee | UNDERPOWERED |
| sspec_f7ced723232cbac818ab4c9f | trade_date_block_shuffle | 9326 | BLOCKED | False | True | surrun_d17cca264c05d9dc03bec9e9 | UNDERPOWERED |
| sspec_8276a4e52e4a76e9dff73973 | trade_date_block_shuffle | 9327 | BLOCKED | False | False | surrun_e107c68de147c86adffc382d | UNDERPOWERED |
| sspec_8276a4e52e4a76e9dff73973 | trade_date_block_shuffle | 9328 | BLOCKED | False | False | surrun_e23c46323fcbf95c459a742c | UNDERPOWERED |
| sspec_8276a4e52e4a76e9dff73973 | trade_date_block_shuffle | 9329 | BLOCKED | False | False | surrun_31a31c77655e23b7eb3e0df8 | UNDERPOWERED |
| sspec_ec1c66fe94928d8f34604662 | trade_date_block_shuffle | 9330 | BLOCKED | False | True | surrun_0861d33d247a4219b996501f | UNDERPOWERED |
| sspec_ec1c66fe94928d8f34604662 | trade_date_block_shuffle | 9331 | BLOCKED | False | True | surrun_9b6cf6db9afdad47d0a6c3ae | UNDERPOWERED |
| sspec_ec1c66fe94928d8f34604662 | trade_date_block_shuffle | 9332 | BLOCKED | False | True | surrun_376f927b51c298341030bd9c | UNDERPOWERED |
| sspec_96302e3c0776733e4916ba88 | trade_date_block_shuffle | 9333 | BLOCKED | False | True | surrun_e96137bb9ef5536a4138a2f1 | UNDERPOWERED |
| sspec_96302e3c0776733e4916ba88 | trade_date_block_shuffle | 9334 | BLOCKED | False | True | surrun_a2194af69010b76598cdda0b | UNDERPOWERED |
| sspec_96302e3c0776733e4916ba88 | trade_date_block_shuffle | 9335 | BLOCKED | False | True | surrun_eccfbfae0703c6f99ef6e675 | UNDERPOWERED |
| sspec_2f8dc92ff7b160bc9c59720e | trade_date_block_shuffle | 9336 | BLOCKED | False | True | surrun_8186f8d8923e558723bb0a87 | UNDERPOWERED |
| sspec_2f8dc92ff7b160bc9c59720e | trade_date_block_shuffle | 9337 | BLOCKED | False | True | surrun_3abf9a0f48d5f0a9efa37d87 | UNDERPOWERED |
| sspec_2f8dc92ff7b160bc9c59720e | trade_date_block_shuffle | 9338 | BLOCKED | False | True | surrun_c4044d9a8ef3a467ac060edf | UNDERPOWERED |
| sspec_805533a61d1974e24b7de56a | trade_date_block_shuffle | 9339 | BLOCKED | False | True | surrun_15ffad970f23f26460a2b9d1 | UNDERPOWERED |
| sspec_805533a61d1974e24b7de56a | trade_date_block_shuffle | 9340 | BLOCKED | False | True | surrun_7a4ebd6477f956d98be62f09 | UNDERPOWERED |
| sspec_805533a61d1974e24b7de56a | trade_date_block_shuffle | 9341 | BLOCKED | False | True | surrun_a9b6172441c0a389919026b9 | UNDERPOWERED |
| sspec_6689490fda783118eaa083cc | trade_date_block_shuffle | 9342 | BLOCKED | False | True | surrun_052fa2ba6d9ef69abdf0aa32 | UNDERPOWERED |
| sspec_6689490fda783118eaa083cc | trade_date_block_shuffle | 9343 | BLOCKED | False | True | surrun_40307a58eb8c59fd39333655 | UNDERPOWERED |
| sspec_6689490fda783118eaa083cc | trade_date_block_shuffle | 9344 | BLOCKED | False | True | surrun_444aa92b57d31b47ab719305 | UNDERPOWERED |
| sspec_3e2434641967d0850a53cce4 | trade_date_block_shuffle | 9345 | BLOCKED | False | False | surrun_1f51fc43d681c9094e73929c | UNDERPOWERED |
| sspec_3e2434641967d0850a53cce4 | trade_date_block_shuffle | 9346 | BLOCKED | False | False | surrun_8e329659905336aa5056cf13 | UNDERPOWERED |
| sspec_3e2434641967d0850a53cce4 | trade_date_block_shuffle | 9347 | BLOCKED | False | False | surrun_7905978eb8871770ac1d8960 | UNDERPOWERED |
| sspec_4803a4bb830a2587d310d3e6 | trade_date_block_shuffle | 9348 | BLOCKED | False | True | surrun_0b79c335083b33fa17fb7f0d | UNDERPOWERED |
| sspec_4803a4bb830a2587d310d3e6 | trade_date_block_shuffle | 9349 | BLOCKED | False | True | surrun_3f7b449e63dcfc1cf5ef3788 | UNDERPOWERED |
| sspec_4803a4bb830a2587d310d3e6 | trade_date_block_shuffle | 9350 | BLOCKED | False | True | surrun_789166bc9ec2954100398d7b | UNDERPOWERED |
| sspec_8058f10a7d10b4f8709c032e | trade_date_block_shuffle | 9351 | BLOCKED | False | True | surrun_7631f5263fef32bbf997d5a3 | UNDERPOWERED |
| sspec_8058f10a7d10b4f8709c032e | trade_date_block_shuffle | 9352 | BLOCKED | False | True | surrun_5a3dad8fc404dbd8a230b706 | UNDERPOWERED |
| sspec_8058f10a7d10b4f8709c032e | trade_date_block_shuffle | 9353 | BLOCKED | False | True | surrun_b3970af3a7dbf9b2a090c7e9 | UNDERPOWERED |
| sspec_ea976eff7c10805318008115 | trade_date_block_shuffle | 9354 | BLOCKED | False | True | surrun_e2b1649df24e7b5a127bedec | UNDERPOWERED |
| sspec_ea976eff7c10805318008115 | trade_date_block_shuffle | 9355 | BLOCKED | False | True | surrun_48cb5245792ffa347b588f6d | UNDERPOWERED |
| sspec_ea976eff7c10805318008115 | trade_date_block_shuffle | 9356 | BLOCKED | False | True | surrun_e6bbe7131a25df2fbe19e9e5 | UNDERPOWERED |
| sspec_664fd2ec34605199bddc71f5 | trade_date_block_shuffle | 9357 | BLOCKED | False | True | surrun_7b87e8452f7febc65b29a9b5 | UNDERPOWERED |
| sspec_664fd2ec34605199bddc71f5 | trade_date_block_shuffle | 9358 | BLOCKED | False | True | surrun_4f27a38137ffe6a916c8d8eb | UNDERPOWERED |
| sspec_664fd2ec34605199bddc71f5 | trade_date_block_shuffle | 9359 | BLOCKED | False | True | surrun_4aed93f9e224d2d63c2887b9 | UNDERPOWERED |
| sspec_500b50da754c088c471180b3 | trade_date_block_shuffle | 9360 | BLOCKED | False | True | surrun_6fdc15ba475b6bed6ed932d4 | UNDERPOWERED |
| sspec_500b50da754c088c471180b3 | trade_date_block_shuffle | 9361 | BLOCKED | False | True | surrun_bddf93151a121de17c4138ed | UNDERPOWERED |
| sspec_500b50da754c088c471180b3 | trade_date_block_shuffle | 9362 | BLOCKED | False | True | surrun_915fd78abb9f88fbc6a18543 | UNDERPOWERED |
| sspec_d635130979c2d445aa1ab1bf | trade_date_block_shuffle | 9363 | BLOCKED | False | False | surrun_a14be0a520c195cdaeb381f4 | UNDERPOWERED |
| sspec_d635130979c2d445aa1ab1bf | trade_date_block_shuffle | 9364 | BLOCKED | False | False | surrun_fdee03812b72e9b7d9de71e0 | UNDERPOWERED |
| sspec_d635130979c2d445aa1ab1bf | trade_date_block_shuffle | 9365 | BLOCKED | False | False | surrun_42beda666df02a82020a7cec | UNDERPOWERED |
| sspec_607281f2beca5838fa6322a4 | trade_date_block_shuffle | 9366 | BLOCKED | False | True | surrun_ec9f74352c5acde1b8efd8ce | UNDERPOWERED |
| sspec_607281f2beca5838fa6322a4 | trade_date_block_shuffle | 9367 | BLOCKED | False | True | surrun_c5760afe193df65f34aa1312 | UNDERPOWERED |
| sspec_607281f2beca5838fa6322a4 | trade_date_block_shuffle | 9368 | BLOCKED | False | True | surrun_a6ce8954e9122e99cdb37ebb | UNDERPOWERED |
| sspec_4107e1c21be02e18c32ce54c | trade_date_block_shuffle | 9369 | BLOCKED | False | True | surrun_099791f38cfec810e47d0717 | UNDERPOWERED |
| sspec_4107e1c21be02e18c32ce54c | trade_date_block_shuffle | 9370 | BLOCKED | False | True | surrun_556c1eaa27835d29fd62f5cc | UNDERPOWERED |
| sspec_4107e1c21be02e18c32ce54c | trade_date_block_shuffle | 9371 | BLOCKED | False | True | surrun_97032ceb0c4f4704e7ad6234 | UNDERPOWERED |
| sspec_9dd9d6a437f591a4c845dd59 | trade_date_block_shuffle | 9372 | BLOCKED | False | True | surrun_cb6a7f4d6da6457b433424f7 | UNDERPOWERED |
| sspec_9dd9d6a437f591a4c845dd59 | trade_date_block_shuffle | 9373 | BLOCKED | False | True | surrun_97eccc575795807e38d3ff6a | UNDERPOWERED |
| sspec_9dd9d6a437f591a4c845dd59 | trade_date_block_shuffle | 9374 | BLOCKED | False | True | surrun_39e296e67e2bfbbacf70e375 | UNDERPOWERED |
| sspec_22c1a59af88123362df72885 | trade_date_block_shuffle | 9375 | BLOCKED | False | True | surrun_dfc67e6767ddd93dab921270 | UNDERPOWERED |
| sspec_22c1a59af88123362df72885 | trade_date_block_shuffle | 9376 | BLOCKED | False | True | surrun_00bd8b8105bac128ac810983 | UNDERPOWERED |
| sspec_22c1a59af88123362df72885 | trade_date_block_shuffle | 9377 | BLOCKED | False | True | surrun_79babcfd4ce09062f3b228c2 | UNDERPOWERED |
| sspec_c57a428627cfea84b5b3583f | trade_date_block_shuffle | 9378 | BLOCKED | False | True | surrun_a41f10addb39777b38bacba3 | UNDERPOWERED |
| sspec_c57a428627cfea84b5b3583f | trade_date_block_shuffle | 9379 | BLOCKED | False | True | surrun_b70bb4cc5a8808c7ef13df68 | UNDERPOWERED |
| sspec_c57a428627cfea84b5b3583f | trade_date_block_shuffle | 9380 | BLOCKED | False | True | surrun_dc636e995f18a209af780eb8 | UNDERPOWERED |
| sspec_2ed13d03d5eb2aae3eb7569e | trade_date_block_shuffle | 9381 | BLOCKED | False | False | surrun_be7fce49525608f8efb69b25 | UNDERPOWERED |
| sspec_2ed13d03d5eb2aae3eb7569e | trade_date_block_shuffle | 9382 | BLOCKED | False | False | surrun_d660877608826c1696c21fce | UNDERPOWERED |
| sspec_2ed13d03d5eb2aae3eb7569e | trade_date_block_shuffle | 9383 | BLOCKED | False | False | surrun_0063c2248b4f1866aa9b89af | UNDERPOWERED |
| sspec_9b2e04d4a78db24fef3c7c9d | trade_date_block_shuffle | 9384 | BLOCKED | False | True | surrun_6cb3a40723cc35c812c6c542 | UNDERPOWERED |
| sspec_9b2e04d4a78db24fef3c7c9d | trade_date_block_shuffle | 9385 | BLOCKED | False | True | surrun_3cf9f7769c0560d46553660d | UNDERPOWERED |
| sspec_9b2e04d4a78db24fef3c7c9d | trade_date_block_shuffle | 9386 | BLOCKED | False | True | surrun_905ee0d150ce591b63d2efe1 | UNDERPOWERED |
| sspec_65fd387a0e89d8a07c492852 | trade_date_block_shuffle | 9387 | BLOCKED | False | True | surrun_ac3b903e404f9a4a42352d02 | UNDERPOWERED |
| sspec_65fd387a0e89d8a07c492852 | trade_date_block_shuffle | 9388 | BLOCKED | False | True | surrun_18e48895b3c2d135acdd49fd | UNDERPOWERED |
| sspec_65fd387a0e89d8a07c492852 | trade_date_block_shuffle | 9389 | BLOCKED | False | True | surrun_2e8db7922111e0070a6b5183 | UNDERPOWERED |
| sspec_dfac8c33d00021ce6f65ab23 | trade_date_block_shuffle | 9390 | BLOCKED | False | True | surrun_65975646c2b396ed797fdb83 | UNDERPOWERED |
| sspec_dfac8c33d00021ce6f65ab23 | trade_date_block_shuffle | 9391 | BLOCKED | False | True | surrun_ce5abe09600b8d5c6eac5fc2 | UNDERPOWERED |
| sspec_dfac8c33d00021ce6f65ab23 | trade_date_block_shuffle | 9392 | BLOCKED | False | True | surrun_b8646f7477e3d703aea56bb2 | UNDERPOWERED |
| sspec_0cca341c1981ae40fcb4aa23 | trade_date_block_shuffle | 9393 | BLOCKED | False | True | surrun_0386d529671e8bdd5cc7c9e8 | UNDERPOWERED |
| sspec_0cca341c1981ae40fcb4aa23 | trade_date_block_shuffle | 9394 | BLOCKED | False | True | surrun_cb3ac7b5b9b5062350ed15f6 | UNDERPOWERED |
| sspec_0cca341c1981ae40fcb4aa23 | trade_date_block_shuffle | 9395 | BLOCKED | False | True | surrun_f0133d161aab8092ad22c21e | UNDERPOWERED |
| sspec_31723a88ffb013bc79eb72d7 | trade_date_block_shuffle | 9396 | BLOCKED | False | True | surrun_7309d3cc56df59d263622051 | UNDERPOWERED |
| sspec_31723a88ffb013bc79eb72d7 | trade_date_block_shuffle | 9397 | BLOCKED | False | True | surrun_831941c6db8f9778da8bf5f8 | UNDERPOWERED |
| sspec_31723a88ffb013bc79eb72d7 | trade_date_block_shuffle | 9398 | BLOCKED | False | True | surrun_cf4bd7190bf5d9f2972a42b6 | UNDERPOWERED |
| sspec_5246ac5c1017861b4ebdb16e | trade_date_block_shuffle | 9399 | BLOCKED | False | False | surrun_0ad43180cbd539da79fd726a | UNDERPOWERED |
| sspec_5246ac5c1017861b4ebdb16e | trade_date_block_shuffle | 9400 | BLOCKED | False | False | surrun_04ffa7c207e25f11b2aef727 | UNDERPOWERED |
| sspec_5246ac5c1017861b4ebdb16e | trade_date_block_shuffle | 9401 | BLOCKED | False | False | surrun_542e7fc5294446aac338c167 | UNDERPOWERED |
| sspec_742ba5985376053665719829 | trade_date_block_shuffle | 9402 | BLOCKED | False | True | surrun_086acf190c8792ef88a42ff5 | UNDERPOWERED |
| sspec_742ba5985376053665719829 | trade_date_block_shuffle | 9403 | BLOCKED | False | True | surrun_d096a66d48b81465cd70420d | UNDERPOWERED |
| sspec_742ba5985376053665719829 | trade_date_block_shuffle | 9404 | BLOCKED | False | True | surrun_07e291a5c18fa586f3d8f6be | UNDERPOWERED |
| sspec_be541cc19c5b11d1db02e10f | trade_date_block_shuffle | 9405 | BLOCKED | False | True | surrun_f9c5e0daec4b2de106a3eba6 | UNDERPOWERED |
| sspec_be541cc19c5b11d1db02e10f | trade_date_block_shuffle | 9406 | BLOCKED | False | True | surrun_fc65e8e9230a0edd5e2d49e4 | UNDERPOWERED |
| sspec_be541cc19c5b11d1db02e10f | trade_date_block_shuffle | 9407 | BLOCKED | False | True | surrun_f71fb070829d42d7f59caf17 | UNDERPOWERED |
| sspec_4de48bb86276badf0efce29f | trade_date_block_shuffle | 9408 | BLOCKED | False | True | surrun_1baceec1f5795965629d4cf6 | UNDERPOWERED |
| sspec_4de48bb86276badf0efce29f | trade_date_block_shuffle | 9409 | BLOCKED | False | True | surrun_52b3cd6731912d15a32c9ea4 | UNDERPOWERED |
| sspec_4de48bb86276badf0efce29f | trade_date_block_shuffle | 9410 | BLOCKED | False | True | surrun_3b5ec2166eb05d30c3a83816 | UNDERPOWERED |
| sspec_1299f057f304ec8777c5654b | trade_date_block_shuffle | 9411 | BLOCKED | False | True | surrun_ae7e9733ba30ee0f20c9c2e8 | UNDERPOWERED |
| sspec_1299f057f304ec8777c5654b | trade_date_block_shuffle | 9412 | BLOCKED | False | True | surrun_daa8a82fb3fa3efd1143bb99 | UNDERPOWERED |
| sspec_1299f057f304ec8777c5654b | trade_date_block_shuffle | 9413 | BLOCKED | False | True | surrun_b8ddc41227aec6ad234bab5a | UNDERPOWERED |
| sspec_20a334cdbbae3a44fdfc3c6e | trade_date_block_shuffle | 9414 | BLOCKED | False | True | surrun_e8d363efbe85389c28959d8c | UNDERPOWERED |
| sspec_20a334cdbbae3a44fdfc3c6e | trade_date_block_shuffle | 9415 | BLOCKED | False | True | surrun_eae71d4d75c0b546439d0fb2 | UNDERPOWERED |
| sspec_20a334cdbbae3a44fdfc3c6e | trade_date_block_shuffle | 9416 | BLOCKED | False | True | surrun_82720451c26b25e4a77568e5 | UNDERPOWERED |
| sspec_304836797f981ff209e65cbd | trade_date_block_shuffle | 9417 | BLOCKED | False | False | surrun_a4ba16c800d5b0d1594de63e | UNDERPOWERED |
| sspec_304836797f981ff209e65cbd | trade_date_block_shuffle | 9418 | BLOCKED | False | False | surrun_0070843806d9a5543a8ded73 | UNDERPOWERED |
| sspec_304836797f981ff209e65cbd | trade_date_block_shuffle | 9419 | BLOCKED | False | False | surrun_500ffcc6457ee1fad7109524 | UNDERPOWERED |
| sspec_556170855949d41f09b47bdd | trade_date_block_shuffle | 9420 | BLOCKED | False | True | surrun_fa73a0c1bacf62e6aba41475 | UNDERPOWERED |
| sspec_556170855949d41f09b47bdd | trade_date_block_shuffle | 9421 | BLOCKED | False | True | surrun_9cf5df902373c2f1df7c7852 | UNDERPOWERED |
| sspec_556170855949d41f09b47bdd | trade_date_block_shuffle | 9422 | BLOCKED | False | True | surrun_dcc6afb947820a9f2746bd2d | UNDERPOWERED |
| sspec_cf26a1d55691480f4a17d291 | trade_date_block_shuffle | 9423 | BLOCKED | False | True | surrun_2283a9e5830801e115cfc6d3 | UNDERPOWERED |
| sspec_cf26a1d55691480f4a17d291 | trade_date_block_shuffle | 9424 | BLOCKED | False | True | surrun_1041cb483b3b0a3679280803 | UNDERPOWERED |
| sspec_cf26a1d55691480f4a17d291 | trade_date_block_shuffle | 9425 | BLOCKED | False | True | surrun_20891c2ec530b6227d340981 | UNDERPOWERED |
| sspec_b4a0574ccf8b6d0b34bbb6b7 | trade_date_block_shuffle | 9426 | BLOCKED | False | True | surrun_28ee8e507a678819accb3010 | UNDERPOWERED |
| sspec_b4a0574ccf8b6d0b34bbb6b7 | trade_date_block_shuffle | 9427 | BLOCKED | False | True | surrun_acb401cfbb7f2b4d1fad5aac | UNDERPOWERED |
| sspec_b4a0574ccf8b6d0b34bbb6b7 | trade_date_block_shuffle | 9428 | BLOCKED | False | True | surrun_56e36ca5820dd2c89a0c14e5 | UNDERPOWERED |
| sspec_dbe15b23d3b0ada31de360e7 | trade_date_block_shuffle | 9429 | BLOCKED | False | True | surrun_c5eb585bc9828371e903700a | UNDERPOWERED |
| sspec_dbe15b23d3b0ada31de360e7 | trade_date_block_shuffle | 9430 | BLOCKED | False | True | surrun_6b64444c17d9e4e4efa433a8 | UNDERPOWERED |
| sspec_dbe15b23d3b0ada31de360e7 | trade_date_block_shuffle | 9431 | BLOCKED | False | True | surrun_7901575e5492eb0c2ef5d764 | UNDERPOWERED |
| sspec_1961204c574bf375b77e51f6 | trade_date_block_shuffle | 9432 | BLOCKED | False | True | surrun_0dec10f9cc7c8dd7f887c350 | UNDERPOWERED |
| sspec_1961204c574bf375b77e51f6 | trade_date_block_shuffle | 9433 | BLOCKED | False | True | surrun_061a1e460a646910e078f4ef | UNDERPOWERED |
| sspec_1961204c574bf375b77e51f6 | trade_date_block_shuffle | 9434 | BLOCKED | False | True | surrun_01a5dfedf885fb6abd004d14 | UNDERPOWERED |
| sspec_93660879d80d93dd00494a3b | trade_date_block_shuffle | 9435 | BLOCKED | False | False | surrun_995712b2952977018bd517c8 | UNDERPOWERED |
| sspec_93660879d80d93dd00494a3b | trade_date_block_shuffle | 9436 | BLOCKED | False | False | surrun_6755f9c3bdb3d052ab1da700 | UNDERPOWERED |
| sspec_93660879d80d93dd00494a3b | trade_date_block_shuffle | 9437 | BLOCKED | False | False | surrun_801c37e6ed343a0edb54e803 | UNDERPOWERED |
| sspec_a5b1c91218c4db4d74d42aa1 | trade_date_block_shuffle | 9438 | BLOCKED | False | True | surrun_1cd60f473c846e710b203c96 | UNDERPOWERED |
| sspec_a5b1c91218c4db4d74d42aa1 | trade_date_block_shuffle | 9439 | BLOCKED | False | True | surrun_7b014a76de2df95a6d386661 | UNDERPOWERED |
| sspec_a5b1c91218c4db4d74d42aa1 | trade_date_block_shuffle | 9440 | BLOCKED | False | True | surrun_1c123e699282d8f2dc3d484e | UNDERPOWERED |
| sspec_c51e447b75baf3b7d5375e5c | trade_date_block_shuffle | 9441 | BLOCKED | False | True | surrun_661aec7c9a5dd7f2b2bf656f | UNDERPOWERED |
| sspec_c51e447b75baf3b7d5375e5c | trade_date_block_shuffle | 9442 | BLOCKED | False | True | surrun_41d956f44a96ecc8ce375337 | UNDERPOWERED |
| sspec_c51e447b75baf3b7d5375e5c | trade_date_block_shuffle | 9443 | BLOCKED | False | True | surrun_ebb8df562e2ebb3dc2ce0bce | UNDERPOWERED |
| sspec_5d92b6eec0a1cb5335f09589 | trade_date_block_shuffle | 9444 | BLOCKED | False | True | surrun_5ab31da4c651d91078b71d6e | UNDERPOWERED |
| sspec_5d92b6eec0a1cb5335f09589 | trade_date_block_shuffle | 9445 | BLOCKED | False | True | surrun_5809c68d4de2561d4dc5c84e | UNDERPOWERED |
| sspec_5d92b6eec0a1cb5335f09589 | trade_date_block_shuffle | 9446 | BLOCKED | False | True | surrun_7916ebc06d40cbdb2ac7c012 | UNDERPOWERED |
| sspec_3005bd42b4a81a45dcc1c678 | trade_date_block_shuffle | 9447 | BLOCKED | False | True | surrun_a2dc5407881c7b06e3cc4e02 | UNDERPOWERED |
| sspec_3005bd42b4a81a45dcc1c678 | trade_date_block_shuffle | 9448 | BLOCKED | False | True | surrun_6b59408456e77180c68ae034 | UNDERPOWERED |
| sspec_3005bd42b4a81a45dcc1c678 | trade_date_block_shuffle | 9449 | BLOCKED | False | True | surrun_dde4922193ed5de9b58e432c | UNDERPOWERED |
| sspec_74c59a1472e9f8f4b36e50b1 | trade_date_block_shuffle | 9450 | BLOCKED | False | True | surrun_4a6b4c252bc3026ddd9267ee | UNDERPOWERED |
| sspec_74c59a1472e9f8f4b36e50b1 | trade_date_block_shuffle | 9451 | BLOCKED | False | True | surrun_fc91a6930e478c8b23bebf93 | UNDERPOWERED |
| sspec_74c59a1472e9f8f4b36e50b1 | trade_date_block_shuffle | 9452 | BLOCKED | False | True | surrun_7bf90d9fc2acfd2b9961ba9a | UNDERPOWERED |
| sspec_45662fbd1f1428c6f86e8601 | trade_date_block_shuffle | 9453 | BLOCKED | False | False | surrun_2f410748b92eb48377e5d502 | UNDERPOWERED |
| sspec_45662fbd1f1428c6f86e8601 | trade_date_block_shuffle | 9454 | BLOCKED | False | False | surrun_8352f9be699d39112a856678 | UNDERPOWERED |
| sspec_45662fbd1f1428c6f86e8601 | trade_date_block_shuffle | 9455 | BLOCKED | False | False | surrun_4774fa13f18d245a2b865b21 | UNDERPOWERED |
| sspec_5876bcedc851c002e9896ff1 | trade_date_block_shuffle | 9456 | BLOCKED | False | True | surrun_bb87d06bfed77772086a31eb | UNDERPOWERED |
| sspec_5876bcedc851c002e9896ff1 | trade_date_block_shuffle | 9457 | BLOCKED | False | True | surrun_e6c82773086e4b708267bff3 | UNDERPOWERED |
| sspec_5876bcedc851c002e9896ff1 | trade_date_block_shuffle | 9458 | BLOCKED | False | True | surrun_a8c823f6335bed8069e35407 | UNDERPOWERED |
| sspec_f3385c773268e35c89f0c3bd | trade_date_block_shuffle | 9459 | BLOCKED | False | True | surrun_4219ead294cfcd9f6264cae8 | UNDERPOWERED |
| sspec_f3385c773268e35c89f0c3bd | trade_date_block_shuffle | 9460 | BLOCKED | False | True | surrun_6008f3ba19e5925b9867211c | UNDERPOWERED |
| sspec_f3385c773268e35c89f0c3bd | trade_date_block_shuffle | 9461 | BLOCKED | False | True | surrun_324bcdd86e70302d0beb30fd | UNDERPOWERED |
| sspec_351fffb2472d57eaf0170cf7 | trade_date_block_shuffle | 9462 | BLOCKED | False | True | surrun_709fcb88fa117ea7b67f58ef | UNDERPOWERED |
| sspec_351fffb2472d57eaf0170cf7 | trade_date_block_shuffle | 9463 | BLOCKED | False | True | surrun_14097f2818ea02cf2e3a274e | UNDERPOWERED |
| sspec_351fffb2472d57eaf0170cf7 | trade_date_block_shuffle | 9464 | BLOCKED | False | True | surrun_ef499ea60926818b19122d0c | UNDERPOWERED |
| sspec_002ef3dffd68f6df7f2a388e | trade_date_block_shuffle | 9465 | BLOCKED | False | True | surrun_1846eeb3111c550aeeb714d6 | UNDERPOWERED |
| sspec_002ef3dffd68f6df7f2a388e | trade_date_block_shuffle | 9466 | BLOCKED | False | True | surrun_3226e3c62e32b7e66e2b6cb0 | UNDERPOWERED |
| sspec_002ef3dffd68f6df7f2a388e | trade_date_block_shuffle | 9467 | BLOCKED | False | True | surrun_8612dab92e0151fd3e339d79 | UNDERPOWERED |
| sspec_0f2610c3c69df504acd95947 | trade_date_block_shuffle | 9468 | BLOCKED | False | True | surrun_f4fc99ef5527336d5f9d7874 | UNDERPOWERED |
| sspec_0f2610c3c69df504acd95947 | trade_date_block_shuffle | 9469 | BLOCKED | False | True | surrun_0c5e348e6ee6339e3d7b266c | UNDERPOWERED |
| sspec_0f2610c3c69df504acd95947 | trade_date_block_shuffle | 9470 | BLOCKED | False | True | surrun_23ebd484d9735f591b042df2 | UNDERPOWERED |
| sspec_a26fb03bcced181c120ed0ed | trade_date_block_shuffle | 9471 | BLOCKED | False | False | surrun_da8e011b9cebb0295a542351 | UNDERPOWERED |
| sspec_a26fb03bcced181c120ed0ed | trade_date_block_shuffle | 9472 | BLOCKED | False | False | surrun_82b45fffeab0720d320b7f41 | UNDERPOWERED |
| sspec_a26fb03bcced181c120ed0ed | trade_date_block_shuffle | 9473 | BLOCKED | False | False | surrun_e8bc7048777aa9cf0d16f890 | UNDERPOWERED |
| sspec_4846d6a1875f10d1168e7086 | trade_date_block_shuffle | 9474 | BLOCKED | False | True | surrun_85ca12bba8224ebb30f301db | UNDERPOWERED |
| sspec_4846d6a1875f10d1168e7086 | trade_date_block_shuffle | 9475 | BLOCKED | False | True | surrun_f839bb6fccfea5758b58caf8 | UNDERPOWERED |
| sspec_4846d6a1875f10d1168e7086 | trade_date_block_shuffle | 9476 | BLOCKED | False | True | surrun_6767913f585eadcbc89f65a2 | UNDERPOWERED |
| sspec_26661510bd05f3235e4f4535 | trade_date_block_shuffle | 9477 | BLOCKED | False | True | surrun_d5827854647dadab3ec8ff95 | UNDERPOWERED |
| sspec_26661510bd05f3235e4f4535 | trade_date_block_shuffle | 9478 | BLOCKED | False | True | surrun_a1e6beb3ec5202b2bbf4d193 | UNDERPOWERED |
| sspec_26661510bd05f3235e4f4535 | trade_date_block_shuffle | 9479 | BLOCKED | False | True | surrun_466c83c15759397439b9d2b5 | UNDERPOWERED |
| sspec_04ff1b30c1c494d13e829c97 | trade_date_block_shuffle | 9480 | BLOCKED | False | True | surrun_1084c8028695857ffd011f7a | UNDERPOWERED |
| sspec_04ff1b30c1c494d13e829c97 | trade_date_block_shuffle | 9481 | BLOCKED | False | True | surrun_f9d4be9f2a95d3ecdc190ef6 | UNDERPOWERED |
| sspec_04ff1b30c1c494d13e829c97 | trade_date_block_shuffle | 9482 | BLOCKED | False | True | surrun_040f220e26e0b2c2f6974392 | UNDERPOWERED |
| sspec_f0780b37428e02e197db56a5 | trade_date_block_shuffle | 9483 | BLOCKED | False | True | surrun_7da260b1dda4e20edd571cb7 | UNDERPOWERED |
| sspec_f0780b37428e02e197db56a5 | trade_date_block_shuffle | 9484 | BLOCKED | False | True | surrun_7e4e9ce2bff31c6ffc0e2817 | UNDERPOWERED |
| sspec_f0780b37428e02e197db56a5 | trade_date_block_shuffle | 9485 | BLOCKED | False | True | surrun_04979cba250163c0e9df3cc4 | UNDERPOWERED |
| sspec_be813c5caad387f10b885016 | trade_date_block_shuffle | 9486 | BLOCKED | False | True | surrun_817f41d82b1e1d7359140eb2 | UNDERPOWERED |
| sspec_be813c5caad387f10b885016 | trade_date_block_shuffle | 9487 | BLOCKED | False | True | surrun_b2bed1c0b77bc83876d95222 | UNDERPOWERED |
| sspec_be813c5caad387f10b885016 | trade_date_block_shuffle | 9488 | BLOCKED | False | True | surrun_005abae970a8af3154cca970 | UNDERPOWERED |
| sspec_2c564ab1343cdf993ede86d1 | trade_date_block_shuffle | 9489 | BLOCKED | False | False | surrun_954ce169d194ab88bb8038a2 | UNDERPOWERED |
| sspec_2c564ab1343cdf993ede86d1 | trade_date_block_shuffle | 9490 | BLOCKED | False | False | surrun_76cf3b83e2b76259f1447135 | UNDERPOWERED |
| sspec_2c564ab1343cdf993ede86d1 | trade_date_block_shuffle | 9491 | BLOCKED | False | False | surrun_6f471539059d2ab0cb06b6b0 | UNDERPOWERED |
| sspec_5b47d7f1344f1a4bc8525d8d | trade_date_block_shuffle | 9492 | BLOCKED | False | True | surrun_fac4b2ed8a61075b4b19d5e1 | UNDERPOWERED |
| sspec_5b47d7f1344f1a4bc8525d8d | trade_date_block_shuffle | 9493 | BLOCKED | False | True | surrun_49fa24492db8798ee2670ad0 | UNDERPOWERED |
| sspec_5b47d7f1344f1a4bc8525d8d | trade_date_block_shuffle | 9494 | BLOCKED | False | True | surrun_fdb2c94a01811d671a53ccfc | UNDERPOWERED |
| sspec_e6f61d582b2c36be920ec304 | trade_date_block_shuffle | 9495 | BLOCKED | False | True | surrun_e06e3af84409fbdb250c0313 | UNDERPOWERED |
| sspec_e6f61d582b2c36be920ec304 | trade_date_block_shuffle | 9496 | BLOCKED | False | True | surrun_45b1ac96747112dc7927670d | UNDERPOWERED |
| sspec_e6f61d582b2c36be920ec304 | trade_date_block_shuffle | 9497 | BLOCKED | False | True | surrun_1a72e8a9bcd4b4db4c1de98a | UNDERPOWERED |
| sspec_ff8497bbde9f35f22ecf5afa | trade_date_block_shuffle | 9498 | BLOCKED | False | True | surrun_3a22944818cd41a773dedee7 | UNDERPOWERED |
| sspec_ff8497bbde9f35f22ecf5afa | trade_date_block_shuffle | 9499 | BLOCKED | False | True | surrun_01eacffe141b353bba9ecb47 | UNDERPOWERED |
| sspec_ff8497bbde9f35f22ecf5afa | trade_date_block_shuffle | 9500 | BLOCKED | False | True | surrun_a4797d618d58d07787a31e4d | UNDERPOWERED |
| sspec_065dc2d7c6ad2247c38617c3 | trade_date_block_shuffle | 9501 | BLOCKED | False | True | surrun_d20053347bf5790250cac523 | UNDERPOWERED |
| sspec_065dc2d7c6ad2247c38617c3 | trade_date_block_shuffle | 9502 | BLOCKED | False | True | surrun_4cd527981cffb222c07692d8 | UNDERPOWERED |
| sspec_065dc2d7c6ad2247c38617c3 | trade_date_block_shuffle | 9503 | BLOCKED | False | True | surrun_13a659a4f6ed59c03b251682 | UNDERPOWERED |
| sspec_d823020ef45ecd4380ec3c3a | trade_date_block_shuffle | 9504 | BLOCKED | False | True | surrun_ba5c9be4890dbc4e314b8a12 | UNDERPOWERED |
| sspec_d823020ef45ecd4380ec3c3a | trade_date_block_shuffle | 9505 | BLOCKED | False | True | surrun_f3adc7cd5b9ea5ed57f6afe6 | UNDERPOWERED |
| sspec_d823020ef45ecd4380ec3c3a | trade_date_block_shuffle | 9506 | BLOCKED | False | True | surrun_1d5612255c6bff03abf2368f | UNDERPOWERED |
| sspec_fe096657b1ea307afd018a2d | trade_date_block_shuffle | 9507 | BLOCKED | False | False | surrun_005a17d86bc1f501f48de0ab | UNDERPOWERED |
| sspec_fe096657b1ea307afd018a2d | trade_date_block_shuffle | 9508 | BLOCKED | False | False | surrun_1e4dfc3e4a2f1c9fe2a9e87b | UNDERPOWERED |
| sspec_fe096657b1ea307afd018a2d | trade_date_block_shuffle | 9509 | BLOCKED | False | False | surrun_34d75ea7d00817888282ff43 | UNDERPOWERED |
| sspec_5398c9ea7c176514a1c71614 | trade_date_block_shuffle | 9510 | BLOCKED | False | True | surrun_340e0bd2ffbf7038aed7f47a | UNDERPOWERED |
| sspec_5398c9ea7c176514a1c71614 | trade_date_block_shuffle | 9511 | BLOCKED | False | True | surrun_9b8219b837426ea260f4b02f | UNDERPOWERED |
| sspec_5398c9ea7c176514a1c71614 | trade_date_block_shuffle | 9512 | BLOCKED | False | True | surrun_277d73ffbfceaa50bae2245f | UNDERPOWERED |
| sspec_f4f3c9e5a93087d1fc7adbee | trade_date_block_shuffle | 9513 | BLOCKED | False | True | surrun_856212b1527c63066741c65e | UNDERPOWERED |
| sspec_f4f3c9e5a93087d1fc7adbee | trade_date_block_shuffle | 9514 | BLOCKED | False | True | surrun_a17bcc5c88556ee45329f652 | UNDERPOWERED |
| sspec_f4f3c9e5a93087d1fc7adbee | trade_date_block_shuffle | 9515 | BLOCKED | False | True | surrun_572d2b1c0752874f3eaea7be | UNDERPOWERED |
| sspec_b580f5e5bd7cbd7ad8b885ba | trade_date_block_shuffle | 9516 | BLOCKED | False | True | surrun_1b0df54dacca5fd57012ad98 | UNDERPOWERED |
| sspec_b580f5e5bd7cbd7ad8b885ba | trade_date_block_shuffle | 9517 | BLOCKED | False | True | surrun_20e73d67bd73f134ad8c087c | UNDERPOWERED |
| sspec_b580f5e5bd7cbd7ad8b885ba | trade_date_block_shuffle | 9518 | BLOCKED | False | True | surrun_5054fad2e1deb78c3989a14c | UNDERPOWERED |
| sspec_db808660aab45cda6464d705 | trade_date_block_shuffle | 9519 | BLOCKED | False | True | surrun_10e6cc8fdd45300e0c4e7c75 | UNDERPOWERED |
| sspec_db808660aab45cda6464d705 | trade_date_block_shuffle | 9520 | BLOCKED | False | True | surrun_081b8b39840dee7845e1d87c | UNDERPOWERED |
| sspec_db808660aab45cda6464d705 | trade_date_block_shuffle | 9521 | BLOCKED | False | True | surrun_1f5d650efc21c6b745130ba7 | UNDERPOWERED |
| sspec_0a6015abd389d9a8945b4455 | trade_date_block_shuffle | 9522 | BLOCKED | False | True | surrun_97d06d207904311f5d74c5e6 | UNDERPOWERED |
| sspec_0a6015abd389d9a8945b4455 | trade_date_block_shuffle | 9523 | BLOCKED | False | True | surrun_373dfd38c3e83072bff93158 | UNDERPOWERED |
| sspec_0a6015abd389d9a8945b4455 | trade_date_block_shuffle | 9524 | BLOCKED | False | True | surrun_7e134c12c6b87688c37fb06a | UNDERPOWERED |
| sspec_c4790e5b972047477664e96a | trade_date_block_shuffle | 9525 | BLOCKED | False | False | surrun_a60f3dfa57683eb08ff6c373 | UNDERPOWERED |
| sspec_c4790e5b972047477664e96a | trade_date_block_shuffle | 9526 | BLOCKED | False | False | surrun_cbe85f14cd64719654652b74 | UNDERPOWERED |
| sspec_c4790e5b972047477664e96a | trade_date_block_shuffle | 9527 | BLOCKED | False | False | surrun_5e106f3631e156f61c05e548 | UNDERPOWERED |
| sspec_b3b33ccaffc002c77d772a88 | trade_date_block_shuffle | 9528 | BLOCKED | False | True | surrun_f7306b5849459f836d5284c6 | UNDERPOWERED |
| sspec_b3b33ccaffc002c77d772a88 | trade_date_block_shuffle | 9529 | BLOCKED | False | True | surrun_6485adcc5b6ed34f22634939 | UNDERPOWERED |
| sspec_b3b33ccaffc002c77d772a88 | trade_date_block_shuffle | 9530 | BLOCKED | False | True | surrun_00641a5ecafa30c267e87ded | UNDERPOWERED |
| sspec_8c006df3c6338474d80e8d20 | trade_date_block_shuffle | 9531 | BLOCKED | False | True | surrun_06c6f2ea08e893e05f555073 | UNDERPOWERED |
| sspec_8c006df3c6338474d80e8d20 | trade_date_block_shuffle | 9532 | BLOCKED | False | True | surrun_ad4bddf564ffe8ee1a343cfb | UNDERPOWERED |
| sspec_8c006df3c6338474d80e8d20 | trade_date_block_shuffle | 9533 | BLOCKED | False | True | surrun_f7533b4d812501976d4dd454 | UNDERPOWERED |
| sspec_ea79b474055f324092758c33 | trade_date_block_shuffle | 9534 | BLOCKED | False | True | surrun_d96008a535db2daf0ab063e7 | UNDERPOWERED |
| sspec_ea79b474055f324092758c33 | trade_date_block_shuffle | 9535 | BLOCKED | False | True | surrun_ebb921220c3005693d896aac | UNDERPOWERED |
| sspec_ea79b474055f324092758c33 | trade_date_block_shuffle | 9536 | BLOCKED | False | True | surrun_12bb4c8d30a4b4221c857a24 | UNDERPOWERED |
| sspec_636f87c6cdc8339b2b527eea | trade_date_block_shuffle | 9537 | BLOCKED | False | True | surrun_2d853ec0cf03ea00d4f89cb5 | UNDERPOWERED |
| sspec_636f87c6cdc8339b2b527eea | trade_date_block_shuffle | 9538 | BLOCKED | False | True | surrun_c63e288f23ff9c11007cced9 | UNDERPOWERED |
| sspec_636f87c6cdc8339b2b527eea | trade_date_block_shuffle | 9539 | BLOCKED | False | True | surrun_dec39d40643b8cd131158129 | UNDERPOWERED |
| sspec_5d1b3bb34fb51da74e6a81aa | trade_date_block_shuffle | 9540 | BLOCKED | False | True | surrun_37f4802880cbf5bc0870f692 | UNDERPOWERED |
| sspec_5d1b3bb34fb51da74e6a81aa | trade_date_block_shuffle | 9541 | BLOCKED | False | True | surrun_16027fe661d000040e31de12 | UNDERPOWERED |
| sspec_5d1b3bb34fb51da74e6a81aa | trade_date_block_shuffle | 9542 | BLOCKED | False | True | surrun_2b2b8ab9ee15ec52af0a4280 | UNDERPOWERED |
| sspec_184ef312d4cacd5c72165927 | trade_date_block_shuffle | 9543 | BLOCKED | False | False | surrun_f33cf607b7a31b75ccc5e1b5 | UNDERPOWERED |
| sspec_184ef312d4cacd5c72165927 | trade_date_block_shuffle | 9544 | BLOCKED | False | False | surrun_0bd7257002430654033a43ad | UNDERPOWERED |
| sspec_184ef312d4cacd5c72165927 | trade_date_block_shuffle | 9545 | BLOCKED | False | False | surrun_207d7a77d75e6a94ac183a78 | UNDERPOWERED |
| sspec_3998608c3cd16ea1c331304a | trade_date_block_shuffle | 9546 | BLOCKED | False | True | surrun_8c06ed23bdb947521a57e5ec | UNDERPOWERED |
| sspec_3998608c3cd16ea1c331304a | trade_date_block_shuffle | 9547 | BLOCKED | False | True | surrun_605d1ed2ab58e80aa446f2f5 | UNDERPOWERED |
| sspec_3998608c3cd16ea1c331304a | trade_date_block_shuffle | 9548 | BLOCKED | False | True | surrun_daef405f9c158c240c716d07 | UNDERPOWERED |
| sspec_d215dbf6b0842c7563e01148 | trade_date_block_shuffle | 9549 | BLOCKED | False | True | surrun_ca9a2ea9fcc3c5a6a96e264e | UNDERPOWERED |
| sspec_d215dbf6b0842c7563e01148 | trade_date_block_shuffle | 9550 | BLOCKED | False | True | surrun_93a4b901efddde58338d6b23 | UNDERPOWERED |
| sspec_d215dbf6b0842c7563e01148 | trade_date_block_shuffle | 9551 | BLOCKED | False | True | surrun_5ff798308da1b311b4a0cab9 | UNDERPOWERED |
| sspec_f8b412aa2ee3c42bc30a733f | trade_date_block_shuffle | 9552 | BLOCKED | False | True | surrun_b32d90cc68ac6bb3f2e8e558 | UNDERPOWERED |
| sspec_f8b412aa2ee3c42bc30a733f | trade_date_block_shuffle | 9553 | BLOCKED | False | True | surrun_a82a4e7dc87dfa8fd8306237 | UNDERPOWERED |
| sspec_f8b412aa2ee3c42bc30a733f | trade_date_block_shuffle | 9554 | BLOCKED | False | True | surrun_41391b358af3d4a8459a0276 | UNDERPOWERED |
| sspec_38130bb1d0490830c52517a9 | trade_date_block_shuffle | 9555 | BLOCKED | False | True | surrun_778eb616614236905c4ab28f | UNDERPOWERED |
| sspec_38130bb1d0490830c52517a9 | trade_date_block_shuffle | 9556 | BLOCKED | False | True | surrun_506701cab40e68ed8ab83aa0 | UNDERPOWERED |
| sspec_38130bb1d0490830c52517a9 | trade_date_block_shuffle | 9557 | BLOCKED | False | True | surrun_a7fa3e53a156b9e7f844b2de | UNDERPOWERED |
| sspec_d0664078d2befab418173b27 | trade_date_block_shuffle | 9558 | BLOCKED | False | True | surrun_00d94ed526ee3573f4de6dfd | UNDERPOWERED |
| sspec_d0664078d2befab418173b27 | trade_date_block_shuffle | 9559 | BLOCKED | False | True | surrun_46a58c23dbe144648057e616 | UNDERPOWERED |
| sspec_d0664078d2befab418173b27 | trade_date_block_shuffle | 9560 | BLOCKED | False | True | surrun_07118fad49cb6724ca3a7b16 | UNDERPOWERED |
| sspec_a6796a695a6c80592f04d075 | trade_date_block_shuffle | 9561 | BLOCKED | False | False | surrun_9e1303ed9f57879a54049296 | UNDERPOWERED |
| sspec_a6796a695a6c80592f04d075 | trade_date_block_shuffle | 9562 | BLOCKED | False | False | surrun_0596d837b4e1a8cece265545 | UNDERPOWERED |
| sspec_a6796a695a6c80592f04d075 | trade_date_block_shuffle | 9563 | BLOCKED | False | False | surrun_72b1eda12b07e14669c8f909 | UNDERPOWERED |
| sspec_fd9befda353435f0d7a33f4a | trade_date_block_shuffle | 9564 | BLOCKED | False | True | surrun_18963df22be85ce027958375 | UNDERPOWERED |
| sspec_fd9befda353435f0d7a33f4a | trade_date_block_shuffle | 9565 | BLOCKED | False | True | surrun_2a3a3c651cb7a592b08a9c11 | UNDERPOWERED |
| sspec_fd9befda353435f0d7a33f4a | trade_date_block_shuffle | 9566 | BLOCKED | False | True | surrun_f8a9373fd746dc28bfc43de4 | UNDERPOWERED |
| sspec_d01bb0bff1ddff4135316028 | trade_date_block_shuffle | 9567 | BLOCKED | False | True | surrun_06b70cdcb801432265bcab28 | UNDERPOWERED |
| sspec_d01bb0bff1ddff4135316028 | trade_date_block_shuffle | 9568 | BLOCKED | False | True | surrun_93f943631d1cad9c59cce1a3 | UNDERPOWERED |
| sspec_d01bb0bff1ddff4135316028 | trade_date_block_shuffle | 9569 | BLOCKED | False | True | surrun_c568138aeb3f9246f09a16a0 | UNDERPOWERED |
| sspec_54ee0b3ed80da440676c8c29 | trade_date_block_shuffle | 9570 | BLOCKED | False | True | surrun_f608797fbed57f6e9fb39b1b | UNDERPOWERED |
| sspec_54ee0b3ed80da440676c8c29 | trade_date_block_shuffle | 9571 | BLOCKED | False | True | surrun_c0a0e5284e15079815e051bf | UNDERPOWERED |
| sspec_54ee0b3ed80da440676c8c29 | trade_date_block_shuffle | 9572 | BLOCKED | False | True | surrun_b148a7a9d515eaa290446581 | UNDERPOWERED |
| sspec_771ab6d42af4e8469b9a5096 | trade_date_block_shuffle | 9573 | BLOCKED | False | True | surrun_c25d67c1c67b5c80e559f22f | UNDERPOWERED |
| sspec_771ab6d42af4e8469b9a5096 | trade_date_block_shuffle | 9574 | BLOCKED | False | True | surrun_3d62eafd993fd10c0de426f3 | UNDERPOWERED |
| sspec_771ab6d42af4e8469b9a5096 | trade_date_block_shuffle | 9575 | BLOCKED | False | True | surrun_dc81aea6fa8858c7bcb6a460 | UNDERPOWERED |
| sspec_4c3105d699c5957104a697bc | trade_date_block_shuffle | 9576 | BLOCKED | False | True | surrun_cf2f99e68d456901048e028b | UNDERPOWERED |
| sspec_4c3105d699c5957104a697bc | trade_date_block_shuffle | 9577 | BLOCKED | False | True | surrun_1cf62e2ae27b16562dbb6f01 | UNDERPOWERED |
| sspec_4c3105d699c5957104a697bc | trade_date_block_shuffle | 9578 | BLOCKED | False | True | surrun_9cb28ecc5bd2661f91cf3f16 | UNDERPOWERED |
| sspec_d4120e7747bee4ee2c84e36c | trade_date_block_shuffle | 9579 | BLOCKED | False | False | surrun_6e8fb540a07f6d77c5a2c84d | UNDERPOWERED |
| sspec_d4120e7747bee4ee2c84e36c | trade_date_block_shuffle | 9580 | BLOCKED | False | False | surrun_2470916bcf3eae2b0c3ee0f2 | UNDERPOWERED |
| sspec_d4120e7747bee4ee2c84e36c | trade_date_block_shuffle | 9581 | BLOCKED | False | False | surrun_75615184b20d7bb1a4d3611a | UNDERPOWERED |
| sspec_26e3e739e1bf8f50fef5fe88 | trade_date_block_shuffle | 9582 | BLOCKED | False | True | surrun_08f5455f48f4d6d1ff2dd780 | UNDERPOWERED |
| sspec_26e3e739e1bf8f50fef5fe88 | trade_date_block_shuffle | 9583 | BLOCKED | False | True | surrun_78de8524a2efdfb4bbba72d8 | UNDERPOWERED |
| sspec_26e3e739e1bf8f50fef5fe88 | trade_date_block_shuffle | 9584 | BLOCKED | False | True | surrun_1ac44941ea750d72a129d29a | UNDERPOWERED |
| sspec_b8f2c2a8368755105d2b4d82 | trade_date_block_shuffle | 9585 | BLOCKED | False | True | surrun_50619d6ef4a17c863ab95c5f | UNDERPOWERED |
| sspec_b8f2c2a8368755105d2b4d82 | trade_date_block_shuffle | 9586 | BLOCKED | False | True | surrun_aa85fdcc67e42c0334da4cfc | UNDERPOWERED |
| sspec_b8f2c2a8368755105d2b4d82 | trade_date_block_shuffle | 9587 | BLOCKED | False | True | surrun_2dca1ca50fabcb4e2738c0d2 | UNDERPOWERED |
| sspec_f4a2854f02095cf852c950fa | trade_date_block_shuffle | 9588 | BLOCKED | False | True | surrun_d25a6e631622508a812aaa07 | UNDERPOWERED |
| sspec_f4a2854f02095cf852c950fa | trade_date_block_shuffle | 9589 | BLOCKED | False | True | surrun_8d9bdbf70459dfe77285d25b | UNDERPOWERED |
| sspec_f4a2854f02095cf852c950fa | trade_date_block_shuffle | 9590 | BLOCKED | False | True | surrun_c1380cad7b84aa7ccaced766 | UNDERPOWERED |
| sspec_70b6f00ffa3f72cf37c75d03 | trade_date_block_shuffle | 9591 | BLOCKED | False | True | surrun_56752e1c46e1da2c474d59c5 | UNDERPOWERED |
| sspec_70b6f00ffa3f72cf37c75d03 | trade_date_block_shuffle | 9592 | BLOCKED | False | True | surrun_950f594e2c880b2a9ccae872 | UNDERPOWERED |
| sspec_70b6f00ffa3f72cf37c75d03 | trade_date_block_shuffle | 9593 | BLOCKED | False | True | surrun_48da2fa80669aac1d5c0db28 | UNDERPOWERED |
| sspec_47a7f29d36706d35623a1838 | trade_date_block_shuffle | 9594 | BLOCKED | False | True | surrun_e2fb7105320f9cfb45b6f211 | UNDERPOWERED |
| sspec_47a7f29d36706d35623a1838 | trade_date_block_shuffle | 9595 | BLOCKED | False | True | surrun_ed4a305f262dd5be144286cc | UNDERPOWERED |
| sspec_47a7f29d36706d35623a1838 | trade_date_block_shuffle | 9596 | BLOCKED | False | True | surrun_c4026cacffd1099969a30273 | UNDERPOWERED |
| sspec_285c69e19ad111290e7bca26 | trade_date_block_shuffle | 9597 | BLOCKED | False | False | surrun_2eed8dd7c850d0dd5c7309f1 | UNDERPOWERED |
| sspec_285c69e19ad111290e7bca26 | trade_date_block_shuffle | 9598 | BLOCKED | False | False | surrun_27b3754e8a42ee2c401ffb24 | UNDERPOWERED |
| sspec_285c69e19ad111290e7bca26 | trade_date_block_shuffle | 9599 | BLOCKED | False | False | surrun_430f873fc7ecf7ab3b890e66 | UNDERPOWERED |
| sspec_f49a16ae0487aed01f5d31ff | trade_date_block_shuffle | 9600 | BLOCKED | False | True | surrun_f68d2c9de162133701024605 | UNDERPOWERED |
| sspec_f49a16ae0487aed01f5d31ff | trade_date_block_shuffle | 9601 | BLOCKED | False | True | surrun_ccc94b49a5467c575363fdc5 | UNDERPOWERED |
| sspec_f49a16ae0487aed01f5d31ff | trade_date_block_shuffle | 9602 | BLOCKED | False | True | surrun_77e062a7c3dd6ba4ff3b5e07 | UNDERPOWERED |
| sspec_aa19848593b5bb715aa189b5 | trade_date_block_shuffle | 9603 | BLOCKED | False | True | surrun_c24d411b47a77d7a5a23d621 | UNDERPOWERED |
| sspec_aa19848593b5bb715aa189b5 | trade_date_block_shuffle | 9604 | BLOCKED | False | True | surrun_ad5a1f80cad07d08ebd6b985 | UNDERPOWERED |
| sspec_aa19848593b5bb715aa189b5 | trade_date_block_shuffle | 9605 | BLOCKED | False | True | surrun_cbf23cc738268a7676a67ada | UNDERPOWERED |
| sspec_1f228d065dadb325eb5b7126 | trade_date_block_shuffle | 9606 | BLOCKED | False | True | surrun_eef919aa88d7fdfca3230824 | UNDERPOWERED |
| sspec_1f228d065dadb325eb5b7126 | trade_date_block_shuffle | 9607 | BLOCKED | False | True | surrun_224262f62ab4509cd95118e2 | UNDERPOWERED |
| sspec_1f228d065dadb325eb5b7126 | trade_date_block_shuffle | 9608 | BLOCKED | False | True | surrun_eeb8c862ddc8541ccce527a7 | UNDERPOWERED |
| sspec_41e47d45e6a2b1a6c8244d15 | trade_date_block_shuffle | 9609 | BLOCKED | False | True | surrun_087d933be2433026aef28e9f | UNDERPOWERED |
| sspec_41e47d45e6a2b1a6c8244d15 | trade_date_block_shuffle | 9610 | BLOCKED | False | True | surrun_a5c3c7c8d152e9c2bcb1bad4 | UNDERPOWERED |
| sspec_41e47d45e6a2b1a6c8244d15 | trade_date_block_shuffle | 9611 | BLOCKED | False | True | surrun_72572e3aea10f68c3168e17f | UNDERPOWERED |
| sspec_80e9443ee06411d84204d9bf | trade_date_block_shuffle | 9612 | BLOCKED | False | True | surrun_2c817e81478b4b8b6f488026 | UNDERPOWERED |
| sspec_80e9443ee06411d84204d9bf | trade_date_block_shuffle | 9613 | BLOCKED | False | True | surrun_9945e1edf66d3fedbecfde1d | UNDERPOWERED |
| sspec_80e9443ee06411d84204d9bf | trade_date_block_shuffle | 9614 | BLOCKED | False | True | surrun_d49c1c4ba98dded86dbe4bc7 | UNDERPOWERED |
| sspec_554b4f96cdbcab3bb7402097 | trade_date_block_shuffle | 9615 | BLOCKED | False | False | surrun_346f4ab94f989062815f3f72 | UNDERPOWERED |
| sspec_554b4f96cdbcab3bb7402097 | trade_date_block_shuffle | 9616 | BLOCKED | False | False | surrun_4e522969a7ce11688c3b583a | UNDERPOWERED |
| sspec_554b4f96cdbcab3bb7402097 | trade_date_block_shuffle | 9617 | BLOCKED | False | False | surrun_e9a4c13f5edafd54b62dea7e | UNDERPOWERED |
| sspec_9963dc5c1e94bb0b4b39259c | trade_date_block_shuffle | 9618 | BLOCKED | False | True | surrun_d8bc7c2c186ecfefe406e649 | UNDERPOWERED |
| sspec_9963dc5c1e94bb0b4b39259c | trade_date_block_shuffle | 9619 | BLOCKED | False | True | surrun_d76f04bf59ce5366f8b33d51 | UNDERPOWERED |
| sspec_9963dc5c1e94bb0b4b39259c | trade_date_block_shuffle | 9620 | BLOCKED | False | True | surrun_b01b9b05db5522a320b56183 | UNDERPOWERED |
| sspec_93890288887c0acf8f7d613e | trade_date_block_shuffle | 9621 | BLOCKED | False | True | surrun_4fb3d15e816b83b820bc07b4 | UNDERPOWERED |
| sspec_93890288887c0acf8f7d613e | trade_date_block_shuffle | 9622 | BLOCKED | False | True | surrun_ba0920a192e799d6769aca30 | UNDERPOWERED |
| sspec_93890288887c0acf8f7d613e | trade_date_block_shuffle | 9623 | BLOCKED | False | True | surrun_4bc7d2b941bb67e87b9a5e84 | UNDERPOWERED |
| sspec_084f472873d857d306f0e195 | trade_date_block_shuffle | 9624 | BLOCKED | False | True | surrun_fa11ef7812f9aa991b21fe57 | UNDERPOWERED |
| sspec_084f472873d857d306f0e195 | trade_date_block_shuffle | 9625 | BLOCKED | False | True | surrun_c13dd09b01081bfef7da2225 | UNDERPOWERED |
| sspec_084f472873d857d306f0e195 | trade_date_block_shuffle | 9626 | BLOCKED | False | True | surrun_a6646b2c7462d2b4751f2e74 | UNDERPOWERED |
| sspec_4fb1beae2da381f510f11652 | trade_date_block_shuffle | 9627 | BLOCKED | False | True | surrun_94e8431c04a4b36b396871e0 | UNDERPOWERED |
| sspec_4fb1beae2da381f510f11652 | trade_date_block_shuffle | 9628 | BLOCKED | False | True | surrun_eb58a964a7e27c380d9fc26d | UNDERPOWERED |
| sspec_4fb1beae2da381f510f11652 | trade_date_block_shuffle | 9629 | BLOCKED | False | True | surrun_5caf459636e4e6ed783e5b99 | UNDERPOWERED |
| sspec_ec135af63f8717d6f58584bc | trade_date_block_shuffle | 9630 | BLOCKED | False | True | surrun_73cb8c0af442bb8a7b03b1dd | UNDERPOWERED |
| sspec_ec135af63f8717d6f58584bc | trade_date_block_shuffle | 9631 | BLOCKED | False | True | surrun_b0a7ab73353fcbce2e273a19 | UNDERPOWERED |
| sspec_ec135af63f8717d6f58584bc | trade_date_block_shuffle | 9632 | BLOCKED | False | True | surrun_049e9a330063dad1dc6303d2 | UNDERPOWERED |
| sspec_695b0b6b9197189be6e2a634 | trade_date_block_shuffle | 9633 | BLOCKED | False | False | surrun_39c86006c4279c73bb6bfa37 | UNDERPOWERED |
| sspec_695b0b6b9197189be6e2a634 | trade_date_block_shuffle | 9634 | BLOCKED | False | False | surrun_3172bb93fa91b2dda8c0f6d5 | UNDERPOWERED |
| sspec_695b0b6b9197189be6e2a634 | trade_date_block_shuffle | 9635 | BLOCKED | False | False | surrun_89d3cef9eddeca62ae02b9dc | UNDERPOWERED |
| sspec_213aa6de8d4fc74089d67853 | trade_date_block_shuffle | 9636 | BLOCKED | False | True | surrun_7e5ee63d903f2056ba2d0888 | UNDERPOWERED |
| sspec_213aa6de8d4fc74089d67853 | trade_date_block_shuffle | 9637 | BLOCKED | False | True | surrun_b527077cae72f53b39e1fe4a | UNDERPOWERED |
| sspec_213aa6de8d4fc74089d67853 | trade_date_block_shuffle | 9638 | BLOCKED | False | True | surrun_21fb7fc6465135d8a6f514ba | UNDERPOWERED |
| sspec_addaade7e5ead29719adf0b2 | trade_date_block_shuffle | 9639 | BLOCKED | False | True | surrun_806e296a51cebf8b7c7c0523 | UNDERPOWERED |
| sspec_addaade7e5ead29719adf0b2 | trade_date_block_shuffle | 9640 | BLOCKED | False | True | surrun_8b9425177c1c56f41dac96fe | UNDERPOWERED |
| sspec_addaade7e5ead29719adf0b2 | trade_date_block_shuffle | 9641 | BLOCKED | False | True | surrun_8c210f5182e729c29e9f376f | UNDERPOWERED |
| sspec_1535d29dc4d77f8e59230e1a | trade_date_block_shuffle | 9642 | BLOCKED | False | True | surrun_054e1f914d627ddeaadd8224 | UNDERPOWERED |
| sspec_1535d29dc4d77f8e59230e1a | trade_date_block_shuffle | 9643 | BLOCKED | False | True | surrun_92b057cddf293a4c9ff5fb1a | UNDERPOWERED |
| sspec_1535d29dc4d77f8e59230e1a | trade_date_block_shuffle | 9644 | BLOCKED | False | True | surrun_bf4c52d22cc1fc740ba2e65c | UNDERPOWERED |
| sspec_83405df2ef3bebb3e6e33875 | trade_date_block_shuffle | 9645 | BLOCKED | False | True | surrun_cafb2016a225cf94d61898c1 | UNDERPOWERED |
| sspec_83405df2ef3bebb3e6e33875 | trade_date_block_shuffle | 9646 | BLOCKED | False | True | surrun_d574fae338c5a1f3f77b1975 | UNDERPOWERED |
| sspec_83405df2ef3bebb3e6e33875 | trade_date_block_shuffle | 9647 | BLOCKED | False | True | surrun_390b62fe4dc70ec88c389e20 | UNDERPOWERED |
| sspec_5eb78fba4f09edef3e87c737 | trade_date_block_shuffle | 9648 | BLOCKED | False | True | surrun_07f0cddd30e11c26d4a0b2fb | UNDERPOWERED |
| sspec_5eb78fba4f09edef3e87c737 | trade_date_block_shuffle | 9649 | BLOCKED | False | True | surrun_3ad2f035beb5776f4782a87f | UNDERPOWERED |
| sspec_5eb78fba4f09edef3e87c737 | trade_date_block_shuffle | 9650 | BLOCKED | False | True | surrun_025fd67026a315e32e9f6c32 | UNDERPOWERED |
| sspec_26f4f6319ac4b2aa48b0d8ee | trade_date_block_shuffle | 9651 | BLOCKED | False | False | surrun_3dd1b7c2773d3896e6fc45f1 | UNDERPOWERED |
| sspec_26f4f6319ac4b2aa48b0d8ee | trade_date_block_shuffle | 9652 | BLOCKED | False | False | surrun_2e72ec3d7d9c23619d3e8189 | UNDERPOWERED |
| sspec_26f4f6319ac4b2aa48b0d8ee | trade_date_block_shuffle | 9653 | BLOCKED | False | False | surrun_3e5c2e0f6bbf7c16eb5d5939 | UNDERPOWERED |
| sspec_506e3508502a09ccb5a439a2 | trade_date_block_shuffle | 9654 | BLOCKED | False | True | surrun_471c608525d08a3ac4f956fd | UNDERPOWERED |
| sspec_506e3508502a09ccb5a439a2 | trade_date_block_shuffle | 9655 | BLOCKED | False | True | surrun_9236a9927d21110885cc1e5c | UNDERPOWERED |
| sspec_506e3508502a09ccb5a439a2 | trade_date_block_shuffle | 9656 | BLOCKED | False | True | surrun_a252c6a75691657e1d8b6737 | UNDERPOWERED |
| sspec_628c432fd006f69de08d8b59 | trade_date_block_shuffle | 9657 | BLOCKED | False | True | surrun_688dcbc6be3720170840dfb2 | UNDERPOWERED |
| sspec_628c432fd006f69de08d8b59 | trade_date_block_shuffle | 9658 | BLOCKED | False | True | surrun_46489f5a5a4cd1fcc8efb19e | UNDERPOWERED |
| sspec_628c432fd006f69de08d8b59 | trade_date_block_shuffle | 9659 | BLOCKED | False | True | surrun_3b5c6d58522eedb7ac4525c9 | UNDERPOWERED |
| sspec_de474aed4cb509f5c30a879f | trade_date_block_shuffle | 9660 | BLOCKED | False | True | surrun_5762c98f18b5f058b0226600 | UNDERPOWERED |
| sspec_de474aed4cb509f5c30a879f | trade_date_block_shuffle | 9661 | BLOCKED | False | True | surrun_30c34e4d94b3d8260cfe8cac | UNDERPOWERED |
| sspec_de474aed4cb509f5c30a879f | trade_date_block_shuffle | 9662 | BLOCKED | False | True | surrun_ca891dcd043c79f8a1d89fa5 | UNDERPOWERED |
| sspec_8507a6e3dcc1b7f2977a2412 | trade_date_block_shuffle | 9663 | BLOCKED | False | True | surrun_3b09ee80d4c798db631a9b1d | UNDERPOWERED |
| sspec_8507a6e3dcc1b7f2977a2412 | trade_date_block_shuffle | 9664 | BLOCKED | False | True | surrun_5f9ee90c4cdf9c5e4cd66816 | UNDERPOWERED |
| sspec_8507a6e3dcc1b7f2977a2412 | trade_date_block_shuffle | 9665 | BLOCKED | False | True | surrun_486ae5df9dbb3efed75d6bac | UNDERPOWERED |
| sspec_a78c1d8a1eb0fb7cc0920de6 | trade_date_block_shuffle | 9666 | BLOCKED | False | True | surrun_9b61da39065059e32ddd9165 | UNDERPOWERED |
| sspec_a78c1d8a1eb0fb7cc0920de6 | trade_date_block_shuffle | 9667 | BLOCKED | False | True | surrun_ec43fb6f60726a34885ff001 | UNDERPOWERED |
| sspec_a78c1d8a1eb0fb7cc0920de6 | trade_date_block_shuffle | 9668 | BLOCKED | False | True | surrun_a3dfaf6a7d3390f8d07a9b7e | UNDERPOWERED |
| sspec_e195b78de7df0dbdf592f8aa | trade_date_block_shuffle | 9669 | BLOCKED | False | False | surrun_3b114c50e0eea9d3109e3952 | UNDERPOWERED |
| sspec_e195b78de7df0dbdf592f8aa | trade_date_block_shuffle | 9670 | BLOCKED | False | False | surrun_c45e2829be5e1cedd48200a0 | UNDERPOWERED |
| sspec_e195b78de7df0dbdf592f8aa | trade_date_block_shuffle | 9671 | BLOCKED | False | False | surrun_bebc8eeaa9ca98041b53aacb | UNDERPOWERED |
| sspec_bb92cb59b890f542415916ec | trade_date_block_shuffle | 9672 | BLOCKED | False | True | surrun_7e4c9f9215d6dcbd3ab39347 | UNDERPOWERED |
| sspec_bb92cb59b890f542415916ec | trade_date_block_shuffle | 9673 | BLOCKED | False | True | surrun_732e4e79d1cffb275af5f443 | UNDERPOWERED |
| sspec_bb92cb59b890f542415916ec | trade_date_block_shuffle | 9674 | BLOCKED | False | True | surrun_af1cf18b436ee8144eafe9df | UNDERPOWERED |
| sspec_c619e94e72d5308c959f41ac | trade_date_block_shuffle | 9675 | BLOCKED | False | True | surrun_0460a86f7d2a73f1b37b3710 | UNDERPOWERED |
| sspec_c619e94e72d5308c959f41ac | trade_date_block_shuffle | 9676 | BLOCKED | False | True | surrun_d336d58124e0de38ef84703c | UNDERPOWERED |
| sspec_c619e94e72d5308c959f41ac | trade_date_block_shuffle | 9677 | BLOCKED | False | True | surrun_919141ff0f6e871d71e3a644 | UNDERPOWERED |
| sspec_f9f9135661b8e6d0e6ed7b2f | trade_date_block_shuffle | 9678 | BLOCKED | False | True | surrun_798ff0a32ab451a2713253ef | UNDERPOWERED |
| sspec_f9f9135661b8e6d0e6ed7b2f | trade_date_block_shuffle | 9679 | BLOCKED | False | True | surrun_ee17312838f54492381605b9 | UNDERPOWERED |
| sspec_f9f9135661b8e6d0e6ed7b2f | trade_date_block_shuffle | 9680 | BLOCKED | False | True | surrun_2b4dd69808f04ee9019b4690 | UNDERPOWERED |
| sspec_6d55ff64b5993e7ab8aaab3a | trade_date_block_shuffle | 9681 | BLOCKED | False | True | surrun_85355bb333286c96ca82fef1 | UNDERPOWERED |
| sspec_6d55ff64b5993e7ab8aaab3a | trade_date_block_shuffle | 9682 | BLOCKED | False | True | surrun_25c9a4611f7d9fdd87cc5005 | UNDERPOWERED |
| sspec_6d55ff64b5993e7ab8aaab3a | trade_date_block_shuffle | 9683 | BLOCKED | False | True | surrun_c0fbe68c1b6a4bfe9e155a12 | UNDERPOWERED |
| sspec_351bf6b67b45e5d341658a00 | trade_date_block_shuffle | 9684 | BLOCKED | False | True | surrun_d2dfcf516fcd867027e11469 | UNDERPOWERED |
| sspec_351bf6b67b45e5d341658a00 | trade_date_block_shuffle | 9685 | BLOCKED | False | True | surrun_842178ed3c51770e948da611 | UNDERPOWERED |
| sspec_351bf6b67b45e5d341658a00 | trade_date_block_shuffle | 9686 | BLOCKED | False | True | surrun_5e0c2a0b2f63c5d961c5fbba | UNDERPOWERED |
| sspec_eab480c2f09bfdad567e2b33 | trade_date_block_shuffle | 9687 | BLOCKED | False | False | surrun_716f587ba7f56ca0104361cb | UNDERPOWERED |
| sspec_eab480c2f09bfdad567e2b33 | trade_date_block_shuffle | 9688 | BLOCKED | False | False | surrun_2bfa8c568a1494bd73e7b853 | UNDERPOWERED |
| sspec_eab480c2f09bfdad567e2b33 | trade_date_block_shuffle | 9689 | BLOCKED | False | False | surrun_282752f094aa877c3c23f1ec | UNDERPOWERED |
| sspec_16b84147002fcd2b3984a6eb | trade_date_block_shuffle | 9690 | BLOCKED | False | True | surrun_73135b9917a091519b1396a8 | UNDERPOWERED |
| sspec_16b84147002fcd2b3984a6eb | trade_date_block_shuffle | 9691 | BLOCKED | False | True | surrun_0d20e658aff67980d2d7bfd3 | UNDERPOWERED |
| sspec_16b84147002fcd2b3984a6eb | trade_date_block_shuffle | 9692 | BLOCKED | False | True | surrun_b2a7e581549e154d9c3bf7ad | UNDERPOWERED |
| sspec_7a44550ed000f189822129fc | trade_date_block_shuffle | 9693 | BLOCKED | False | True | surrun_47f210c9a802fdef7e1e6109 | UNDERPOWERED |
| sspec_7a44550ed000f189822129fc | trade_date_block_shuffle | 9694 | BLOCKED | False | True | surrun_9aee7ca8d979fcfe534740fd | UNDERPOWERED |
| sspec_7a44550ed000f189822129fc | trade_date_block_shuffle | 9695 | BLOCKED | False | True | surrun_715d59d470f0f4e3da31dfc8 | UNDERPOWERED |
| sspec_21ecc3664800a63c27d3aac9 | trade_date_block_shuffle | 9696 | BLOCKED | False | True | surrun_3b57c732e9f063ed7ee0bc0a | UNDERPOWERED |
| sspec_21ecc3664800a63c27d3aac9 | trade_date_block_shuffle | 9697 | BLOCKED | False | True | surrun_af3d1c7c520143082379664d | UNDERPOWERED |
| sspec_21ecc3664800a63c27d3aac9 | trade_date_block_shuffle | 9698 | BLOCKED | False | True | surrun_5b78906313444e8d0817ea51 | UNDERPOWERED |
| sspec_9b7e3ab5a5c6bc26813fca1d | trade_date_block_shuffle | 9699 | BLOCKED | False | True | surrun_05c92d0a9df79f7e87d2db9e | UNDERPOWERED |
| sspec_9b7e3ab5a5c6bc26813fca1d | trade_date_block_shuffle | 9700 | BLOCKED | False | True | surrun_ec4472230d5cfa7fb9cdd784 | UNDERPOWERED |
| sspec_9b7e3ab5a5c6bc26813fca1d | trade_date_block_shuffle | 9701 | BLOCKED | False | True | surrun_ff0ca94ba0f2e5e6fc430bb7 | UNDERPOWERED |
| sspec_e8d6fa29005c5ac73d0a3970 | trade_date_block_shuffle | 9702 | BLOCKED | False | True | surrun_40aa8a06392da9001117c69a | UNDERPOWERED |
| sspec_e8d6fa29005c5ac73d0a3970 | trade_date_block_shuffle | 9703 | BLOCKED | False | True | surrun_cc9f55d9b0e5d7035b6bf8e8 | UNDERPOWERED |
| sspec_e8d6fa29005c5ac73d0a3970 | trade_date_block_shuffle | 9704 | BLOCKED | False | True | surrun_2da26b4df639862c0f7beb48 | UNDERPOWERED |
| sspec_80f0071931072e4717e09bb9 | trade_date_block_shuffle | 9705 | BLOCKED | False | False | surrun_de7723dbb7e487e39bfed49f | UNDERPOWERED |
| sspec_80f0071931072e4717e09bb9 | trade_date_block_shuffle | 9706 | BLOCKED | False | False | surrun_a56395bafe246283aa681393 | UNDERPOWERED |
| sspec_80f0071931072e4717e09bb9 | trade_date_block_shuffle | 9707 | BLOCKED | False | False | surrun_1111f3fe6978b67eb3c61cfc | UNDERPOWERED |
| sspec_5b21922442fb7b0aa261628f | trade_date_block_shuffle | 9708 | BLOCKED | False | True | surrun_b47c103863ccd174cee187ab | UNDERPOWERED |
| sspec_5b21922442fb7b0aa261628f | trade_date_block_shuffle | 9709 | BLOCKED | False | True | surrun_e28aad26a7e3aaa7ea088641 | UNDERPOWERED |
| sspec_5b21922442fb7b0aa261628f | trade_date_block_shuffle | 9710 | BLOCKED | False | True | surrun_51e8494fbd52676ea8228f40 | UNDERPOWERED |
| sspec_949477f2a35b9d18511a8dd4 | trade_date_block_shuffle | 9711 | BLOCKED | False | True | surrun_f521f17c6491f0016dca1193 | UNDERPOWERED |
| sspec_949477f2a35b9d18511a8dd4 | trade_date_block_shuffle | 9712 | BLOCKED | False | True | surrun_0980ed10de2ffc9ac6ef16f8 | UNDERPOWERED |
| sspec_949477f2a35b9d18511a8dd4 | trade_date_block_shuffle | 9713 | BLOCKED | False | True | surrun_75e102c0fece64a4e2b6bb3f | UNDERPOWERED |
| sspec_555a0f22c2a7e5756d00223f | trade_date_block_shuffle | 9714 | BLOCKED | False | True | surrun_e774618a8a22e80b800ac524 | UNDERPOWERED |
| sspec_555a0f22c2a7e5756d00223f | trade_date_block_shuffle | 9715 | BLOCKED | False | True | surrun_c5ccef243ae4a9ddfa650dd9 | UNDERPOWERED |
| sspec_555a0f22c2a7e5756d00223f | trade_date_block_shuffle | 9716 | BLOCKED | False | True | surrun_9484e572621ac6b4b7765b4a | UNDERPOWERED |
| sspec_e779096edc5474e881518f4e | trade_date_block_shuffle | 9717 | BLOCKED | False | True | surrun_ea2e648050da37b644bb51de | UNDERPOWERED |
| sspec_e779096edc5474e881518f4e | trade_date_block_shuffle | 9718 | BLOCKED | False | True | surrun_89a9a3d14c7374f3ea9fca8a | UNDERPOWERED |
| sspec_e779096edc5474e881518f4e | trade_date_block_shuffle | 9719 | BLOCKED | False | True | surrun_d69664e9c01c5ef4a23ac70d | UNDERPOWERED |
| sspec_cf5d9d0c7f963d4bfc761ccd | trade_date_block_shuffle | 9720 | BLOCKED | False | True | surrun_4a8af974455fa3f9a76de82a | UNDERPOWERED |
| sspec_cf5d9d0c7f963d4bfc761ccd | trade_date_block_shuffle | 9721 | BLOCKED | False | True | surrun_3f227e5365170b3dad7c8b87 | UNDERPOWERED |
| sspec_cf5d9d0c7f963d4bfc761ccd | trade_date_block_shuffle | 9722 | BLOCKED | False | True | surrun_83ca64ba1775ad71570f5336 | UNDERPOWERED |
| sspec_d98d99865ada446673549c5c | trade_date_block_shuffle | 9723 | BLOCKED | False | False | surrun_2ece392eb3222d92758d3b7a | UNDERPOWERED |
| sspec_d98d99865ada446673549c5c | trade_date_block_shuffle | 9724 | BLOCKED | False | False | surrun_050439ee4929cfe673c1d3ff | UNDERPOWERED |
| sspec_d98d99865ada446673549c5c | trade_date_block_shuffle | 9725 | BLOCKED | False | False | surrun_53ac26fa5aff190bbd952175 | UNDERPOWERED |
| sspec_d5170abfd49dd2f44784b3f9 | trade_date_block_shuffle | 9726 | BLOCKED | False | True | surrun_8c461c8355d74abfd3399597 | UNDERPOWERED |
| sspec_d5170abfd49dd2f44784b3f9 | trade_date_block_shuffle | 9727 | BLOCKED | False | True | surrun_5b65070b704b2c2fa3ae3d01 | UNDERPOWERED |
| sspec_d5170abfd49dd2f44784b3f9 | trade_date_block_shuffle | 9728 | BLOCKED | False | True | surrun_2464ae57337928b58932b856 | UNDERPOWERED |
| sspec_14055ed00532925f29c89d9b | trade_date_block_shuffle | 9729 | BLOCKED | False | True | surrun_b05391257be56053f77ef611 | UNDERPOWERED |
| sspec_14055ed00532925f29c89d9b | trade_date_block_shuffle | 9730 | BLOCKED | False | True | surrun_e2bdd995fe82f7a7ed145d95 | UNDERPOWERED |
| sspec_14055ed00532925f29c89d9b | trade_date_block_shuffle | 9731 | BLOCKED | False | True | surrun_13aa555ab0e30cc9f72dd72f | UNDERPOWERED |
| sspec_00145d6a03aacd0a55a51408 | trade_date_block_bootstrap | 9732 | BLOCKED | False | True | surrun_124f2513bda8fb12e4019f9a | UNDERPOWERED |
| sspec_00145d6a03aacd0a55a51408 | trade_date_block_bootstrap | 9733 | BLOCKED | False | True | surrun_4bd2314391ccdd8266c47c21 | UNDERPOWERED |
| sspec_00145d6a03aacd0a55a51408 | trade_date_block_bootstrap | 9734 | BLOCKED | False | True | surrun_85d2d45d6b6bc6e0b147c8a6 | UNDERPOWERED |
| sspec_e0e747934316205e581e3230 | trade_date_block_bootstrap | 9735 | BLOCKED | False | True | surrun_22a4a4a6c521d85e73ac6e34 | UNDERPOWERED |
| sspec_e0e747934316205e581e3230 | trade_date_block_bootstrap | 9736 | BLOCKED | False | True | surrun_45532178a59a82f0c8c7ac22 | UNDERPOWERED |
| sspec_e0e747934316205e581e3230 | trade_date_block_bootstrap | 9737 | BLOCKED | False | True | surrun_536bcbf072df7c3abb614b7b | UNDERPOWERED |
| sspec_5b5f138648471fb016566a96 | trade_date_block_bootstrap | 9738 | BLOCKED | False | True | surrun_c2e6cb634f8c4d1b98920405 | UNDERPOWERED |
| sspec_5b5f138648471fb016566a96 | trade_date_block_bootstrap | 9739 | BLOCKED | False | True | surrun_2c1c4120f1465a1e70993d0a | UNDERPOWERED |
| sspec_5b5f138648471fb016566a96 | trade_date_block_bootstrap | 9740 | BLOCKED | False | True | surrun_9100c0e124f48cee7278303c | UNDERPOWERED |
| sspec_641962ccd20eafc96802967f | trade_date_block_bootstrap | 9741 | BLOCKED | False | False | surrun_4a5c155485e526541f055775 | UNDERPOWERED |
| sspec_641962ccd20eafc96802967f | trade_date_block_bootstrap | 9742 | BLOCKED | False | False | surrun_2fcc0651a392a3325cd713af | UNDERPOWERED |
| sspec_641962ccd20eafc96802967f | trade_date_block_bootstrap | 9743 | BLOCKED | False | False | surrun_55250f18a59cb03eedd7bebc | UNDERPOWERED |
| sspec_130a69ed17c50e2ea8e1550b | trade_date_block_bootstrap | 9744 | BLOCKED | False | True | surrun_421bb1fd83b573c1cc3ec517 | UNDERPOWERED |
| sspec_130a69ed17c50e2ea8e1550b | trade_date_block_bootstrap | 9745 | BLOCKED | False | True | surrun_b6f27a0dd3b5d9689691ddd3 | UNDERPOWERED |
| sspec_130a69ed17c50e2ea8e1550b | trade_date_block_bootstrap | 9746 | BLOCKED | False | True | surrun_b04d0268ffa2bc2785fdc01d | UNDERPOWERED |
| sspec_005843739d7960855d199691 | trade_date_block_bootstrap | 9747 | BLOCKED | False | True | surrun_5d22b53acbe76fc30d47c1b6 | UNDERPOWERED |
| sspec_005843739d7960855d199691 | trade_date_block_bootstrap | 9748 | BLOCKED | False | True | surrun_3b83cf6f7f8d9a0d58f76d61 | UNDERPOWERED |
| sspec_005843739d7960855d199691 | trade_date_block_bootstrap | 9749 | BLOCKED | False | True | surrun_c81ab4ebfa9fae421888f87e | UNDERPOWERED |
| sspec_1d2ea6eeab7c66800c18eb3c | trade_date_block_bootstrap | 9750 | BLOCKED | False | True | surrun_14d92c44e8814c3898207efd | UNDERPOWERED |
| sspec_1d2ea6eeab7c66800c18eb3c | trade_date_block_bootstrap | 9751 | BLOCKED | False | True | surrun_33ce6dd216eb2b9ca9302b64 | UNDERPOWERED |
| sspec_1d2ea6eeab7c66800c18eb3c | trade_date_block_bootstrap | 9752 | BLOCKED | False | True | surrun_8df40a5e84967719535e49a5 | UNDERPOWERED |
| sspec_7447452da67d19f4bdabe883 | trade_date_block_bootstrap | 9753 | BLOCKED | False | True | surrun_f889316aa37f3d171a8a6c03 | UNDERPOWERED |
| sspec_7447452da67d19f4bdabe883 | trade_date_block_bootstrap | 9754 | BLOCKED | False | True | surrun_7269e11def56c532d49080ca | UNDERPOWERED |
| sspec_7447452da67d19f4bdabe883 | trade_date_block_bootstrap | 9755 | BLOCKED | False | True | surrun_7917a637d4926789bfc18f43 | UNDERPOWERED |
| sspec_f7ced723232cbac818ab4c9f | trade_date_block_bootstrap | 9756 | BLOCKED | False | True | surrun_bb2110e004632182528b69f3 | UNDERPOWERED |
| sspec_f7ced723232cbac818ab4c9f | trade_date_block_bootstrap | 9757 | BLOCKED | False | True | surrun_bcae672e07f625c0f505bc9e | UNDERPOWERED |
| sspec_f7ced723232cbac818ab4c9f | trade_date_block_bootstrap | 9758 | BLOCKED | False | True | surrun_5f20a44e071ed314282e4ca0 | UNDERPOWERED |
| sspec_8276a4e52e4a76e9dff73973 | trade_date_block_bootstrap | 9759 | BLOCKED | False | False | surrun_bf97a35d7fc4ca9b885bd6dc | UNDERPOWERED |
| sspec_8276a4e52e4a76e9dff73973 | trade_date_block_bootstrap | 9760 | BLOCKED | False | False | surrun_e9bca77224d26851b83491f0 | UNDERPOWERED |
| sspec_8276a4e52e4a76e9dff73973 | trade_date_block_bootstrap | 9761 | BLOCKED | False | False | surrun_a0036c23d75d3ac3da76fe5b | UNDERPOWERED |
| sspec_ec1c66fe94928d8f34604662 | trade_date_block_bootstrap | 9762 | BLOCKED | False | True | surrun_ce74707fc8b7a10eb54ab343 | UNDERPOWERED |
| sspec_ec1c66fe94928d8f34604662 | trade_date_block_bootstrap | 9763 | BLOCKED | False | True | surrun_86e5cc925bb56f95e7f8ed98 | UNDERPOWERED |
| sspec_ec1c66fe94928d8f34604662 | trade_date_block_bootstrap | 9764 | BLOCKED | False | True | surrun_37317551b3e660e2a3cee715 | UNDERPOWERED |
| sspec_96302e3c0776733e4916ba88 | trade_date_block_bootstrap | 9765 | BLOCKED | False | True | surrun_acda92fc92e5d3b3a753038e | UNDERPOWERED |
| sspec_96302e3c0776733e4916ba88 | trade_date_block_bootstrap | 9766 | BLOCKED | False | True | surrun_aacd35137e045520c077d520 | UNDERPOWERED |
| sspec_96302e3c0776733e4916ba88 | trade_date_block_bootstrap | 9767 | BLOCKED | False | True | surrun_0a7651c5649ba23d1e810346 | UNDERPOWERED |
| sspec_2f8dc92ff7b160bc9c59720e | trade_date_block_bootstrap | 9768 | BLOCKED | False | True | surrun_67e49e1eabebcd7ca0375647 | UNDERPOWERED |
| sspec_2f8dc92ff7b160bc9c59720e | trade_date_block_bootstrap | 9769 | BLOCKED | False | True | surrun_5642e24807c9768f52d6ea5d | UNDERPOWERED |
| sspec_2f8dc92ff7b160bc9c59720e | trade_date_block_bootstrap | 9770 | BLOCKED | False | True | surrun_a84d94abf8ca4121ed2c4338 | UNDERPOWERED |
| sspec_805533a61d1974e24b7de56a | trade_date_block_bootstrap | 9771 | BLOCKED | False | True | surrun_9b979ce760e190d922cdc09b | UNDERPOWERED |
| sspec_805533a61d1974e24b7de56a | trade_date_block_bootstrap | 9772 | BLOCKED | False | True | surrun_0e2ad69750ff3297d8280208 | UNDERPOWERED |
| sspec_805533a61d1974e24b7de56a | trade_date_block_bootstrap | 9773 | BLOCKED | False | True | surrun_83613f7d9ee593eea58ed3eb | UNDERPOWERED |
| sspec_6689490fda783118eaa083cc | trade_date_block_bootstrap | 9774 | BLOCKED | False | True | surrun_bec7be49e5d0677702cb527b | UNDERPOWERED |
| sspec_6689490fda783118eaa083cc | trade_date_block_bootstrap | 9775 | BLOCKED | False | True | surrun_1570c58a11d24f909920084c | UNDERPOWERED |
| sspec_6689490fda783118eaa083cc | trade_date_block_bootstrap | 9776 | BLOCKED | False | True | surrun_bead51c478d8bf7e512cd3ad | UNDERPOWERED |
| sspec_3e2434641967d0850a53cce4 | trade_date_block_bootstrap | 9777 | BLOCKED | False | False | surrun_5d302413f88208a072e4d181 | UNDERPOWERED |
| sspec_3e2434641967d0850a53cce4 | trade_date_block_bootstrap | 9778 | BLOCKED | False | False | surrun_ec2cf22972de9e949e76da12 | UNDERPOWERED |
| sspec_3e2434641967d0850a53cce4 | trade_date_block_bootstrap | 9779 | BLOCKED | False | False | surrun_5de9427aa64edab35a999e26 | UNDERPOWERED |
| sspec_4803a4bb830a2587d310d3e6 | trade_date_block_bootstrap | 9780 | BLOCKED | False | True | surrun_0897a65ccfcc2f1465f55c8a | UNDERPOWERED |
| sspec_4803a4bb830a2587d310d3e6 | trade_date_block_bootstrap | 9781 | BLOCKED | False | True | surrun_65eaa41f10068b787a4aa72c | UNDERPOWERED |
| sspec_4803a4bb830a2587d310d3e6 | trade_date_block_bootstrap | 9782 | BLOCKED | False | True | surrun_f7435d7d4520614d75e452fb | UNDERPOWERED |
| sspec_8058f10a7d10b4f8709c032e | trade_date_block_bootstrap | 9783 | BLOCKED | False | True | surrun_f7deb94acfd5fe6b0e13bc5b | UNDERPOWERED |
| sspec_8058f10a7d10b4f8709c032e | trade_date_block_bootstrap | 9784 | BLOCKED | False | True | surrun_808355be62ed39406109a738 | UNDERPOWERED |
| sspec_8058f10a7d10b4f8709c032e | trade_date_block_bootstrap | 9785 | BLOCKED | False | True | surrun_c2a7c04b36ca6ed39b04a25a | UNDERPOWERED |
| sspec_ea976eff7c10805318008115 | trade_date_block_bootstrap | 9786 | BLOCKED | False | True | surrun_d540831b95a7c31abc0dea37 | UNDERPOWERED |
| sspec_ea976eff7c10805318008115 | trade_date_block_bootstrap | 9787 | BLOCKED | False | True | surrun_5133de8fac53ff69856d0675 | UNDERPOWERED |
| sspec_ea976eff7c10805318008115 | trade_date_block_bootstrap | 9788 | BLOCKED | False | True | surrun_87907db74052e692b6072c74 | UNDERPOWERED |
| sspec_664fd2ec34605199bddc71f5 | trade_date_block_bootstrap | 9789 | BLOCKED | False | True | surrun_e4dfd5f6209fdca228cff741 | UNDERPOWERED |
| sspec_664fd2ec34605199bddc71f5 | trade_date_block_bootstrap | 9790 | BLOCKED | False | True | surrun_9f48e17226fe0fb207ef3924 | UNDERPOWERED |
| sspec_664fd2ec34605199bddc71f5 | trade_date_block_bootstrap | 9791 | BLOCKED | False | True | surrun_0e6ab1484d2a9a7c7d02a55a | UNDERPOWERED |
| sspec_500b50da754c088c471180b3 | trade_date_block_bootstrap | 9792 | BLOCKED | False | True | surrun_9c5faa3a65d2e4155600a37a | UNDERPOWERED |
| sspec_500b50da754c088c471180b3 | trade_date_block_bootstrap | 9793 | BLOCKED | False | True | surrun_02452a26231cbd09a5f5637a | UNDERPOWERED |
| sspec_500b50da754c088c471180b3 | trade_date_block_bootstrap | 9794 | BLOCKED | False | True | surrun_24de78668507b73d2a0feb91 | UNDERPOWERED |
| sspec_d635130979c2d445aa1ab1bf | trade_date_block_bootstrap | 9795 | BLOCKED | False | False | surrun_7e5708a5d4a4931d5892bc81 | UNDERPOWERED |
| sspec_d635130979c2d445aa1ab1bf | trade_date_block_bootstrap | 9796 | BLOCKED | False | False | surrun_7f55318ba823c47d5d5241bf | UNDERPOWERED |
| sspec_d635130979c2d445aa1ab1bf | trade_date_block_bootstrap | 9797 | BLOCKED | False | False | surrun_0e52dcb372afff6626702548 | UNDERPOWERED |
| sspec_607281f2beca5838fa6322a4 | trade_date_block_bootstrap | 9798 | BLOCKED | False | True | surrun_0f8279bae3767819febcbcc9 | UNDERPOWERED |
| sspec_607281f2beca5838fa6322a4 | trade_date_block_bootstrap | 9799 | BLOCKED | False | True | surrun_bae7f389a61f9a840d228596 | UNDERPOWERED |
| sspec_607281f2beca5838fa6322a4 | trade_date_block_bootstrap | 9800 | BLOCKED | False | True | surrun_dedc1412a0ff1c5a04ef2dcc | UNDERPOWERED |
| sspec_4107e1c21be02e18c32ce54c | trade_date_block_bootstrap | 9801 | BLOCKED | False | True | surrun_e4886ac93e4dd6bee9adfb83 | UNDERPOWERED |
| sspec_4107e1c21be02e18c32ce54c | trade_date_block_bootstrap | 9802 | BLOCKED | False | True | surrun_b890bb07d3f91bf938842400 | UNDERPOWERED |
| sspec_4107e1c21be02e18c32ce54c | trade_date_block_bootstrap | 9803 | BLOCKED | False | True | surrun_8e6b454c36327b5a61c995fe | UNDERPOWERED |
| sspec_9dd9d6a437f591a4c845dd59 | trade_date_block_bootstrap | 9804 | BLOCKED | False | True | surrun_c95877ab4d189de0ac0b4e1f | UNDERPOWERED |
| sspec_9dd9d6a437f591a4c845dd59 | trade_date_block_bootstrap | 9805 | BLOCKED | False | True | surrun_02c33063267722aca676afcb | UNDERPOWERED |
| sspec_9dd9d6a437f591a4c845dd59 | trade_date_block_bootstrap | 9806 | BLOCKED | False | True | surrun_c30da9da614090d96c76e3bd | UNDERPOWERED |
| sspec_22c1a59af88123362df72885 | trade_date_block_bootstrap | 9807 | BLOCKED | False | True | surrun_6dc444706f65977ca0ccc971 | UNDERPOWERED |
| sspec_22c1a59af88123362df72885 | trade_date_block_bootstrap | 9808 | BLOCKED | False | True | surrun_e52f82f42306c3297322697e | UNDERPOWERED |
| sspec_22c1a59af88123362df72885 | trade_date_block_bootstrap | 9809 | BLOCKED | False | True | surrun_12d1b8f59ee8eb9ca6a8c606 | UNDERPOWERED |
| sspec_c57a428627cfea84b5b3583f | trade_date_block_bootstrap | 9810 | BLOCKED | False | True | surrun_83c16f52ebdaa90d13f3cba2 | UNDERPOWERED |
| sspec_c57a428627cfea84b5b3583f | trade_date_block_bootstrap | 9811 | BLOCKED | False | True | surrun_ce0dc0f1afd5c1989b53d192 | UNDERPOWERED |
| sspec_c57a428627cfea84b5b3583f | trade_date_block_bootstrap | 9812 | BLOCKED | False | True | surrun_380445e8a6f5ec5fc332594f | UNDERPOWERED |
| sspec_2ed13d03d5eb2aae3eb7569e | trade_date_block_bootstrap | 9813 | BLOCKED | False | False | surrun_54347bea3b32574ddb2afabc | UNDERPOWERED |
| sspec_2ed13d03d5eb2aae3eb7569e | trade_date_block_bootstrap | 9814 | BLOCKED | False | False | surrun_2398d2364b58bc6790faadf2 | UNDERPOWERED |
| sspec_2ed13d03d5eb2aae3eb7569e | trade_date_block_bootstrap | 9815 | BLOCKED | False | False | surrun_80280f9a19655b38a812512b | UNDERPOWERED |
| sspec_9b2e04d4a78db24fef3c7c9d | trade_date_block_bootstrap | 9816 | BLOCKED | False | True | surrun_56d062b7f46d5c99fd149c22 | UNDERPOWERED |
| sspec_9b2e04d4a78db24fef3c7c9d | trade_date_block_bootstrap | 9817 | BLOCKED | False | True | surrun_4b343fbc50d18db949f67ec4 | UNDERPOWERED |
| sspec_9b2e04d4a78db24fef3c7c9d | trade_date_block_bootstrap | 9818 | BLOCKED | False | True | surrun_f7230c11823d2d1f252f45f2 | UNDERPOWERED |
| sspec_65fd387a0e89d8a07c492852 | trade_date_block_bootstrap | 9819 | BLOCKED | False | True | surrun_f6b116a774987694d440bbc0 | UNDERPOWERED |
| sspec_65fd387a0e89d8a07c492852 | trade_date_block_bootstrap | 9820 | BLOCKED | False | True | surrun_77e68fd40730a60f62c67b65 | UNDERPOWERED |
| sspec_65fd387a0e89d8a07c492852 | trade_date_block_bootstrap | 9821 | BLOCKED | False | True | surrun_ba64ff2d1549fcacbed5c111 | UNDERPOWERED |
| sspec_dfac8c33d00021ce6f65ab23 | trade_date_block_bootstrap | 9822 | BLOCKED | False | True | surrun_569fc04eb8744f8a723fb0a2 | UNDERPOWERED |
| sspec_dfac8c33d00021ce6f65ab23 | trade_date_block_bootstrap | 9823 | BLOCKED | False | True | surrun_65f68cac583c7f18a2ce4830 | UNDERPOWERED |
| sspec_dfac8c33d00021ce6f65ab23 | trade_date_block_bootstrap | 9824 | BLOCKED | False | True | surrun_dec0433c6d0c7bfa222ce67f | UNDERPOWERED |
| sspec_0cca341c1981ae40fcb4aa23 | trade_date_block_bootstrap | 9825 | BLOCKED | False | True | surrun_11679584a947d0597a98c3b4 | UNDERPOWERED |
| sspec_0cca341c1981ae40fcb4aa23 | trade_date_block_bootstrap | 9826 | BLOCKED | False | True | surrun_3f2fc7a96e4e0d4bf031544a | UNDERPOWERED |
| sspec_0cca341c1981ae40fcb4aa23 | trade_date_block_bootstrap | 9827 | BLOCKED | False | True | surrun_7507f2046e71845804029da9 | UNDERPOWERED |
| sspec_31723a88ffb013bc79eb72d7 | trade_date_block_bootstrap | 9828 | BLOCKED | False | True | surrun_c942632a51707022f1329074 | UNDERPOWERED |
| sspec_31723a88ffb013bc79eb72d7 | trade_date_block_bootstrap | 9829 | BLOCKED | False | True | surrun_551bb120c6a6ca0a0fa67b0d | UNDERPOWERED |
| sspec_31723a88ffb013bc79eb72d7 | trade_date_block_bootstrap | 9830 | BLOCKED | False | True | surrun_f82a08cc35893f88835ccef7 | UNDERPOWERED |
| sspec_5246ac5c1017861b4ebdb16e | trade_date_block_bootstrap | 9831 | BLOCKED | False | False | surrun_0861c85c2b3bd76b7d1bf838 | UNDERPOWERED |
| sspec_5246ac5c1017861b4ebdb16e | trade_date_block_bootstrap | 9832 | BLOCKED | False | False | surrun_cc144c49bf9d548e5e793d66 | UNDERPOWERED |
| sspec_5246ac5c1017861b4ebdb16e | trade_date_block_bootstrap | 9833 | BLOCKED | False | False | surrun_967dd35315d7664bad92f0d4 | UNDERPOWERED |
| sspec_742ba5985376053665719829 | trade_date_block_bootstrap | 9834 | BLOCKED | False | True | surrun_593c4542ddc676f1658aac10 | UNDERPOWERED |
| sspec_742ba5985376053665719829 | trade_date_block_bootstrap | 9835 | BLOCKED | False | True | surrun_f82003e986edbd71043b4622 | UNDERPOWERED |
| sspec_742ba5985376053665719829 | trade_date_block_bootstrap | 9836 | BLOCKED | False | True | surrun_e0acc51fa138c98188002763 | UNDERPOWERED |
| sspec_be541cc19c5b11d1db02e10f | trade_date_block_bootstrap | 9837 | BLOCKED | False | True | surrun_6f98ce3aa11891d1563ead71 | UNDERPOWERED |
| sspec_be541cc19c5b11d1db02e10f | trade_date_block_bootstrap | 9838 | BLOCKED | False | True | surrun_c27c6447b343edcb29845b9f | UNDERPOWERED |
| sspec_be541cc19c5b11d1db02e10f | trade_date_block_bootstrap | 9839 | BLOCKED | False | True | surrun_563ca995cfbea545a3ef8dab | UNDERPOWERED |
| sspec_4de48bb86276badf0efce29f | trade_date_block_bootstrap | 9840 | BLOCKED | False | True | surrun_e7b8afd35a2fd918b31883b1 | UNDERPOWERED |
| sspec_4de48bb86276badf0efce29f | trade_date_block_bootstrap | 9841 | BLOCKED | False | True | surrun_202e4794344a648a4c4973e3 | UNDERPOWERED |
| sspec_4de48bb86276badf0efce29f | trade_date_block_bootstrap | 9842 | BLOCKED | False | True | surrun_e7a7153cf18791a555e8f280 | UNDERPOWERED |
| sspec_1299f057f304ec8777c5654b | trade_date_block_bootstrap | 9843 | BLOCKED | False | True | surrun_b2d7845c2b4e9220faa04f0d | UNDERPOWERED |
| sspec_1299f057f304ec8777c5654b | trade_date_block_bootstrap | 9844 | BLOCKED | False | True | surrun_bbff9f3a21459a1d569cb86d | UNDERPOWERED |
| sspec_1299f057f304ec8777c5654b | trade_date_block_bootstrap | 9845 | BLOCKED | False | True | surrun_cfb4a2a0546228441ad4f310 | UNDERPOWERED |
| sspec_20a334cdbbae3a44fdfc3c6e | trade_date_block_bootstrap | 9846 | BLOCKED | False | True | surrun_913e7b564482f16ab515dfd4 | UNDERPOWERED |
| sspec_20a334cdbbae3a44fdfc3c6e | trade_date_block_bootstrap | 9847 | BLOCKED | False | True | surrun_ac9d6dcde22041132cd1186f | UNDERPOWERED |
| sspec_20a334cdbbae3a44fdfc3c6e | trade_date_block_bootstrap | 9848 | BLOCKED | False | True | surrun_feb196b3fd26f6677c25bf56 | UNDERPOWERED |
| sspec_304836797f981ff209e65cbd | trade_date_block_bootstrap | 9849 | BLOCKED | False | False | surrun_6286f3df09b614dde2dec9fb | UNDERPOWERED |
| sspec_304836797f981ff209e65cbd | trade_date_block_bootstrap | 9850 | BLOCKED | False | False | surrun_0e7dd04024b99011dfa19502 | UNDERPOWERED |
| sspec_304836797f981ff209e65cbd | trade_date_block_bootstrap | 9851 | BLOCKED | False | False | surrun_2d742c01ce653de0b6196fa5 | UNDERPOWERED |
| sspec_556170855949d41f09b47bdd | trade_date_block_bootstrap | 9852 | BLOCKED | False | True | surrun_444daf0f1b3204bbb38e400a | UNDERPOWERED |
| sspec_556170855949d41f09b47bdd | trade_date_block_bootstrap | 9853 | BLOCKED | False | True | surrun_9eca647b4a904cf96318788f | UNDERPOWERED |
| sspec_556170855949d41f09b47bdd | trade_date_block_bootstrap | 9854 | BLOCKED | False | True | surrun_49e915b393b282d7b766ac26 | UNDERPOWERED |
| sspec_cf26a1d55691480f4a17d291 | trade_date_block_bootstrap | 9855 | BLOCKED | False | True | surrun_8e70aae283722fb82386839f | UNDERPOWERED |
| sspec_cf26a1d55691480f4a17d291 | trade_date_block_bootstrap | 9856 | BLOCKED | False | True | surrun_bcdac739e25589060c35a269 | UNDERPOWERED |
| sspec_cf26a1d55691480f4a17d291 | trade_date_block_bootstrap | 9857 | BLOCKED | False | True | surrun_79c6147cdd721286bb02287d | UNDERPOWERED |
| sspec_b4a0574ccf8b6d0b34bbb6b7 | trade_date_block_bootstrap | 9858 | BLOCKED | False | True | surrun_6ca6554755cdc1ec407ad847 | UNDERPOWERED |
| sspec_b4a0574ccf8b6d0b34bbb6b7 | trade_date_block_bootstrap | 9859 | BLOCKED | False | True | surrun_aa836453a115eeda71680eaf | UNDERPOWERED |
| sspec_b4a0574ccf8b6d0b34bbb6b7 | trade_date_block_bootstrap | 9860 | BLOCKED | False | True | surrun_083c70618680202199c6d76c | UNDERPOWERED |
| sspec_dbe15b23d3b0ada31de360e7 | trade_date_block_bootstrap | 9861 | BLOCKED | False | True | surrun_f25f7c74f33da1bc65cfe1e1 | UNDERPOWERED |
| sspec_dbe15b23d3b0ada31de360e7 | trade_date_block_bootstrap | 9862 | BLOCKED | False | True | surrun_ca35b1cfcc0f2c77aae1ce13 | UNDERPOWERED |
| sspec_dbe15b23d3b0ada31de360e7 | trade_date_block_bootstrap | 9863 | BLOCKED | False | True | surrun_725155ad2615fe72d9af6e69 | UNDERPOWERED |
| sspec_1961204c574bf375b77e51f6 | trade_date_block_bootstrap | 9864 | BLOCKED | False | True | surrun_a5e734e6105d1a3545cb5655 | UNDERPOWERED |
| sspec_1961204c574bf375b77e51f6 | trade_date_block_bootstrap | 9865 | BLOCKED | False | True | surrun_313f8d7f470f7d23a8696bd4 | UNDERPOWERED |
| sspec_1961204c574bf375b77e51f6 | trade_date_block_bootstrap | 9866 | BLOCKED | False | True | surrun_33e386750ffec235102b08bb | UNDERPOWERED |
| sspec_93660879d80d93dd00494a3b | trade_date_block_bootstrap | 9867 | BLOCKED | False | False | surrun_08ee6806d1c35cdf9c0d6dbb | UNDERPOWERED |
| sspec_93660879d80d93dd00494a3b | trade_date_block_bootstrap | 9868 | BLOCKED | False | False | surrun_ca25315d664804928dac51a5 | UNDERPOWERED |
| sspec_93660879d80d93dd00494a3b | trade_date_block_bootstrap | 9869 | BLOCKED | False | False | surrun_12639958162eccd867f05e2c | UNDERPOWERED |
| sspec_a5b1c91218c4db4d74d42aa1 | trade_date_block_bootstrap | 9870 | BLOCKED | False | True | surrun_b75f92b91c237bc34b3b7b87 | UNDERPOWERED |
| sspec_a5b1c91218c4db4d74d42aa1 | trade_date_block_bootstrap | 9871 | BLOCKED | False | True | surrun_07d7863306fc6604a03267e2 | UNDERPOWERED |
| sspec_a5b1c91218c4db4d74d42aa1 | trade_date_block_bootstrap | 9872 | BLOCKED | False | True | surrun_fcf7aafe71a2da1558ee669c | UNDERPOWERED |
| sspec_c51e447b75baf3b7d5375e5c | trade_date_block_bootstrap | 9873 | BLOCKED | False | True | surrun_e771f89bc5722e0b88cc8b98 | UNDERPOWERED |
| sspec_c51e447b75baf3b7d5375e5c | trade_date_block_bootstrap | 9874 | BLOCKED | False | True | surrun_4ed29e31dc623d43a810ec3d | UNDERPOWERED |
| sspec_c51e447b75baf3b7d5375e5c | trade_date_block_bootstrap | 9875 | BLOCKED | False | True | surrun_6c585b4217ccf75730d71d43 | UNDERPOWERED |
| sspec_5d92b6eec0a1cb5335f09589 | trade_date_block_bootstrap | 9876 | BLOCKED | False | True | surrun_d847355c77daa687146cfe76 | UNDERPOWERED |
| sspec_5d92b6eec0a1cb5335f09589 | trade_date_block_bootstrap | 9877 | BLOCKED | False | True | surrun_340a64dd7ec5cdb46ec10732 | UNDERPOWERED |
| sspec_5d92b6eec0a1cb5335f09589 | trade_date_block_bootstrap | 9878 | BLOCKED | False | True | surrun_89ebda9ca53c4e5b0d70103e | UNDERPOWERED |
| sspec_3005bd42b4a81a45dcc1c678 | trade_date_block_bootstrap | 9879 | BLOCKED | False | True | surrun_bd376f6596515ef3ffa00f0d | UNDERPOWERED |
| sspec_3005bd42b4a81a45dcc1c678 | trade_date_block_bootstrap | 9880 | BLOCKED | False | True | surrun_e45f7c3a2b0311294e8a7d90 | UNDERPOWERED |
| sspec_3005bd42b4a81a45dcc1c678 | trade_date_block_bootstrap | 9881 | BLOCKED | False | True | surrun_44cc580166bd189c37fab7fb | UNDERPOWERED |
| sspec_74c59a1472e9f8f4b36e50b1 | trade_date_block_bootstrap | 9882 | BLOCKED | False | True | surrun_1ed271dc0ea0f6efbede5826 | UNDERPOWERED |
| sspec_74c59a1472e9f8f4b36e50b1 | trade_date_block_bootstrap | 9883 | BLOCKED | False | True | surrun_b09115141fb64de6e9611bc2 | UNDERPOWERED |
| sspec_74c59a1472e9f8f4b36e50b1 | trade_date_block_bootstrap | 9884 | BLOCKED | False | True | surrun_1e139971ab4bd57487b82710 | UNDERPOWERED |
| sspec_45662fbd1f1428c6f86e8601 | trade_date_block_bootstrap | 9885 | BLOCKED | False | False | surrun_92d7fd66b4528968991c9b10 | UNDERPOWERED |
| sspec_45662fbd1f1428c6f86e8601 | trade_date_block_bootstrap | 9886 | BLOCKED | False | False | surrun_06c4fe227e1c67feb498efdb | UNDERPOWERED |
| sspec_45662fbd1f1428c6f86e8601 | trade_date_block_bootstrap | 9887 | BLOCKED | False | False | surrun_ef2103491d4482a964c0ff5d | UNDERPOWERED |
| sspec_5876bcedc851c002e9896ff1 | trade_date_block_bootstrap | 9888 | BLOCKED | False | True | surrun_9259dcb588e8483db800c9f4 | UNDERPOWERED |
| sspec_5876bcedc851c002e9896ff1 | trade_date_block_bootstrap | 9889 | BLOCKED | False | True | surrun_4fb82589e843dad70e5eeeec | UNDERPOWERED |
| sspec_5876bcedc851c002e9896ff1 | trade_date_block_bootstrap | 9890 | BLOCKED | False | True | surrun_3ed2a506fe3edc878113c9aa | UNDERPOWERED |
| sspec_f3385c773268e35c89f0c3bd | trade_date_block_bootstrap | 9891 | BLOCKED | False | True | surrun_760f09f2eb29cc2d1ad6aacc | UNDERPOWERED |
| sspec_f3385c773268e35c89f0c3bd | trade_date_block_bootstrap | 9892 | BLOCKED | False | True | surrun_b647acbe5c8d9d550d30f6e3 | UNDERPOWERED |
| sspec_f3385c773268e35c89f0c3bd | trade_date_block_bootstrap | 9893 | BLOCKED | False | True | surrun_3aac7752d27d1f345303c939 | UNDERPOWERED |
| sspec_351fffb2472d57eaf0170cf7 | trade_date_block_bootstrap | 9894 | BLOCKED | False | True | surrun_a735bc90b6fadb11a19f6700 | UNDERPOWERED |
| sspec_351fffb2472d57eaf0170cf7 | trade_date_block_bootstrap | 9895 | BLOCKED | False | True | surrun_dd246ccaea081497a7f0b91b | UNDERPOWERED |
| sspec_351fffb2472d57eaf0170cf7 | trade_date_block_bootstrap | 9896 | BLOCKED | False | True | surrun_3283876f3b5ace9353c60e27 | UNDERPOWERED |
| sspec_002ef3dffd68f6df7f2a388e | trade_date_block_bootstrap | 9897 | BLOCKED | False | True | surrun_bda5dffbface04801206bbb7 | UNDERPOWERED |
| sspec_002ef3dffd68f6df7f2a388e | trade_date_block_bootstrap | 9898 | BLOCKED | False | True | surrun_c869483be0e9f443e7843f60 | UNDERPOWERED |
| sspec_002ef3dffd68f6df7f2a388e | trade_date_block_bootstrap | 9899 | BLOCKED | False | True | surrun_01e705e7abae26b35c880426 | UNDERPOWERED |
| sspec_0f2610c3c69df504acd95947 | trade_date_block_bootstrap | 9900 | BLOCKED | False | True | surrun_ad856f2701bfb0a572a38766 | UNDERPOWERED |
| sspec_0f2610c3c69df504acd95947 | trade_date_block_bootstrap | 9901 | BLOCKED | False | True | surrun_5ebd7bfd41baef7585db2ea4 | UNDERPOWERED |
| sspec_0f2610c3c69df504acd95947 | trade_date_block_bootstrap | 9902 | BLOCKED | False | True | surrun_eaf15f1d337040ba59beb053 | UNDERPOWERED |
| sspec_a26fb03bcced181c120ed0ed | trade_date_block_bootstrap | 9903 | BLOCKED | False | False | surrun_11e1c0480f3621ab8a294ba1 | UNDERPOWERED |
| sspec_a26fb03bcced181c120ed0ed | trade_date_block_bootstrap | 9904 | BLOCKED | False | False | surrun_b29d8c83280b954ba5e3eb37 | UNDERPOWERED |
| sspec_a26fb03bcced181c120ed0ed | trade_date_block_bootstrap | 9905 | BLOCKED | False | False | surrun_eee17e41901e948027aab107 | UNDERPOWERED |
| sspec_4846d6a1875f10d1168e7086 | trade_date_block_bootstrap | 9906 | BLOCKED | False | True | surrun_210fa2a70bfc7103ab0eb1f7 | UNDERPOWERED |
| sspec_4846d6a1875f10d1168e7086 | trade_date_block_bootstrap | 9907 | BLOCKED | False | True | surrun_bfca14c4fe32c13269e3f58c | UNDERPOWERED |
| sspec_4846d6a1875f10d1168e7086 | trade_date_block_bootstrap | 9908 | BLOCKED | False | True | surrun_b599b883f25ab0a89b8ec89c | UNDERPOWERED |
| sspec_26661510bd05f3235e4f4535 | trade_date_block_bootstrap | 9909 | BLOCKED | False | True | surrun_f383326b8fb5babd429fc03e | UNDERPOWERED |
| sspec_26661510bd05f3235e4f4535 | trade_date_block_bootstrap | 9910 | BLOCKED | False | True | surrun_c015a8b97d6f1069393672ab | UNDERPOWERED |
| sspec_26661510bd05f3235e4f4535 | trade_date_block_bootstrap | 9911 | BLOCKED | False | True | surrun_278a81ebb74ce7a59d5ed935 | UNDERPOWERED |
| sspec_04ff1b30c1c494d13e829c97 | trade_date_block_bootstrap | 9912 | BLOCKED | False | True | surrun_965136f5372616facc284dcb | UNDERPOWERED |
| sspec_04ff1b30c1c494d13e829c97 | trade_date_block_bootstrap | 9913 | BLOCKED | False | True | surrun_f47e311d2796ce3502d85975 | UNDERPOWERED |
| sspec_04ff1b30c1c494d13e829c97 | trade_date_block_bootstrap | 9914 | BLOCKED | False | True | surrun_360d7f191bb3c0d7fcc4699d | UNDERPOWERED |
| sspec_f0780b37428e02e197db56a5 | trade_date_block_bootstrap | 9915 | BLOCKED | False | True | surrun_c9748b885be850516dcac52a | UNDERPOWERED |
| sspec_f0780b37428e02e197db56a5 | trade_date_block_bootstrap | 9916 | BLOCKED | False | True | surrun_1a9a6c6e0d50cbba8806758e | UNDERPOWERED |
| sspec_f0780b37428e02e197db56a5 | trade_date_block_bootstrap | 9917 | BLOCKED | False | True | surrun_90cdcb1cbc3317d6119f0855 | UNDERPOWERED |
| sspec_be813c5caad387f10b885016 | trade_date_block_bootstrap | 9918 | BLOCKED | False | True | surrun_dcde6a3e025acc322e9dcc0f | UNDERPOWERED |
| sspec_be813c5caad387f10b885016 | trade_date_block_bootstrap | 9919 | BLOCKED | False | True | surrun_443cddb1e34e21c83526a0cc | UNDERPOWERED |
| sspec_be813c5caad387f10b885016 | trade_date_block_bootstrap | 9920 | BLOCKED | False | True | surrun_705d24112471d6978cd9c9fb | UNDERPOWERED |
| sspec_2c564ab1343cdf993ede86d1 | trade_date_block_bootstrap | 9921 | BLOCKED | False | False | surrun_1972efc8d8de7bcd227fa487 | UNDERPOWERED |
| sspec_2c564ab1343cdf993ede86d1 | trade_date_block_bootstrap | 9922 | BLOCKED | False | False | surrun_3239b2cb85faa83e40ff0cf5 | UNDERPOWERED |
| sspec_2c564ab1343cdf993ede86d1 | trade_date_block_bootstrap | 9923 | BLOCKED | False | False | surrun_63f34f42aa3eba7858f095cf | UNDERPOWERED |
| sspec_5b47d7f1344f1a4bc8525d8d | trade_date_block_bootstrap | 9924 | BLOCKED | False | True | surrun_2de4fb85a5cadfa29940914b | UNDERPOWERED |
| sspec_5b47d7f1344f1a4bc8525d8d | trade_date_block_bootstrap | 9925 | BLOCKED | False | True | surrun_c29dcda6ccc22a0d3dfbe407 | UNDERPOWERED |
| sspec_5b47d7f1344f1a4bc8525d8d | trade_date_block_bootstrap | 9926 | BLOCKED | False | True | surrun_8f7bd90f32bf32cee2ef3614 | UNDERPOWERED |
| sspec_e6f61d582b2c36be920ec304 | trade_date_block_bootstrap | 9927 | BLOCKED | False | True | surrun_88b89b8db6138a73a798a87f | UNDERPOWERED |
| sspec_e6f61d582b2c36be920ec304 | trade_date_block_bootstrap | 9928 | BLOCKED | False | True | surrun_f4c0836206513607444316b7 | UNDERPOWERED |
| sspec_e6f61d582b2c36be920ec304 | trade_date_block_bootstrap | 9929 | BLOCKED | False | True | surrun_5789936988a9a6d86348bd9c | UNDERPOWERED |
| sspec_ff8497bbde9f35f22ecf5afa | trade_date_block_bootstrap | 9930 | BLOCKED | False | True | surrun_4571859101edd35f54799204 | UNDERPOWERED |
| sspec_ff8497bbde9f35f22ecf5afa | trade_date_block_bootstrap | 9931 | BLOCKED | False | True | surrun_610db63906e18b6b025a4ca5 | UNDERPOWERED |
| sspec_ff8497bbde9f35f22ecf5afa | trade_date_block_bootstrap | 9932 | BLOCKED | False | True | surrun_21ed7ab45b4d8a1c5db7fdb9 | UNDERPOWERED |
| sspec_065dc2d7c6ad2247c38617c3 | trade_date_block_bootstrap | 9933 | BLOCKED | False | True | surrun_44c1a52ccc95170c949e1d18 | UNDERPOWERED |
| sspec_065dc2d7c6ad2247c38617c3 | trade_date_block_bootstrap | 9934 | BLOCKED | False | True | surrun_8998a5e8d9b7346eff23caa2 | UNDERPOWERED |
| sspec_065dc2d7c6ad2247c38617c3 | trade_date_block_bootstrap | 9935 | BLOCKED | False | True | surrun_92b03536e1b53995b3286af5 | UNDERPOWERED |
| sspec_d823020ef45ecd4380ec3c3a | trade_date_block_bootstrap | 9936 | BLOCKED | False | True | surrun_1a987f900fe1daa8780b746b | UNDERPOWERED |
| sspec_d823020ef45ecd4380ec3c3a | trade_date_block_bootstrap | 9937 | BLOCKED | False | True | surrun_a1ff465875c634faae3e8ab0 | UNDERPOWERED |
| sspec_d823020ef45ecd4380ec3c3a | trade_date_block_bootstrap | 9938 | BLOCKED | False | True | surrun_e55e13a7baef86d1e54354e8 | UNDERPOWERED |
| sspec_fe096657b1ea307afd018a2d | trade_date_block_bootstrap | 9939 | BLOCKED | False | False | surrun_b4cc9ce4b5efc15b71fe0c44 | UNDERPOWERED |
| sspec_fe096657b1ea307afd018a2d | trade_date_block_bootstrap | 9940 | BLOCKED | False | False | surrun_be86f898fc5683d94de7dd81 | UNDERPOWERED |
| sspec_fe096657b1ea307afd018a2d | trade_date_block_bootstrap | 9941 | BLOCKED | False | False | surrun_949987c57bd69df75b388047 | UNDERPOWERED |
| sspec_5398c9ea7c176514a1c71614 | trade_date_block_bootstrap | 9942 | BLOCKED | False | True | surrun_c7b109f052c60a060ae7a57b | UNDERPOWERED |
| sspec_5398c9ea7c176514a1c71614 | trade_date_block_bootstrap | 9943 | BLOCKED | False | True | surrun_16bae448c88ecfcc7f63fcf6 | UNDERPOWERED |
| sspec_5398c9ea7c176514a1c71614 | trade_date_block_bootstrap | 9944 | BLOCKED | False | True | surrun_146152c489665d44bada995b | UNDERPOWERED |
| sspec_f4f3c9e5a93087d1fc7adbee | trade_date_block_bootstrap | 9945 | BLOCKED | False | True | surrun_11e5407367c51239ee72c388 | UNDERPOWERED |
| sspec_f4f3c9e5a93087d1fc7adbee | trade_date_block_bootstrap | 9946 | BLOCKED | False | True | surrun_987dec3e82dfe22f7e076a62 | UNDERPOWERED |
| sspec_f4f3c9e5a93087d1fc7adbee | trade_date_block_bootstrap | 9947 | BLOCKED | False | True | surrun_b400297a47a769c9a696d534 | UNDERPOWERED |
| sspec_b580f5e5bd7cbd7ad8b885ba | trade_date_block_bootstrap | 9948 | BLOCKED | False | True | surrun_1cae725b422879d6ea80248d | UNDERPOWERED |
| sspec_b580f5e5bd7cbd7ad8b885ba | trade_date_block_bootstrap | 9949 | BLOCKED | False | True | surrun_d58bbe06fe81e18f8e2d13b3 | UNDERPOWERED |
| sspec_b580f5e5bd7cbd7ad8b885ba | trade_date_block_bootstrap | 9950 | BLOCKED | False | True | surrun_f3ecb5a2eee61d282b168bbf | UNDERPOWERED |
| sspec_db808660aab45cda6464d705 | trade_date_block_bootstrap | 9951 | BLOCKED | False | True | surrun_a24b9920d8801bd7b57e38b4 | UNDERPOWERED |
| sspec_db808660aab45cda6464d705 | trade_date_block_bootstrap | 9952 | BLOCKED | False | True | surrun_e22beb7d7f4c665d378cd0c5 | UNDERPOWERED |
| sspec_db808660aab45cda6464d705 | trade_date_block_bootstrap | 9953 | BLOCKED | False | True | surrun_538dcd42e19d3c842bfe105a | UNDERPOWERED |
| sspec_0a6015abd389d9a8945b4455 | trade_date_block_bootstrap | 9954 | BLOCKED | False | True | surrun_3e55a34124af4051b2deef51 | UNDERPOWERED |
| sspec_0a6015abd389d9a8945b4455 | trade_date_block_bootstrap | 9955 | BLOCKED | False | True | surrun_3497a8668f8554f8ac5b9840 | UNDERPOWERED |
| sspec_0a6015abd389d9a8945b4455 | trade_date_block_bootstrap | 9956 | BLOCKED | False | True | surrun_a99ca9108380813f71c9bcf1 | UNDERPOWERED |
| sspec_c4790e5b972047477664e96a | trade_date_block_bootstrap | 9957 | BLOCKED | False | False | surrun_7d2018da2bfa1acc93ebcd31 | UNDERPOWERED |
| sspec_c4790e5b972047477664e96a | trade_date_block_bootstrap | 9958 | BLOCKED | False | False | surrun_2a4420464a7367edb68b9533 | UNDERPOWERED |
| sspec_c4790e5b972047477664e96a | trade_date_block_bootstrap | 9959 | BLOCKED | False | False | surrun_25dfd0e410e0d750354c6907 | UNDERPOWERED |
| sspec_b3b33ccaffc002c77d772a88 | trade_date_block_bootstrap | 9960 | BLOCKED | False | True | surrun_21386305edcf5cd1fa3f0ca9 | UNDERPOWERED |
| sspec_b3b33ccaffc002c77d772a88 | trade_date_block_bootstrap | 9961 | BLOCKED | False | True | surrun_6304b7b009ee93bbb4e81621 | UNDERPOWERED |
| sspec_b3b33ccaffc002c77d772a88 | trade_date_block_bootstrap | 9962 | BLOCKED | False | True | surrun_6622b6715f987d7dfb2170f6 | UNDERPOWERED |
| sspec_8c006df3c6338474d80e8d20 | trade_date_block_bootstrap | 9963 | BLOCKED | False | True | surrun_5919f16d1c54920502eb0284 | UNDERPOWERED |
| sspec_8c006df3c6338474d80e8d20 | trade_date_block_bootstrap | 9964 | BLOCKED | False | True | surrun_32125ad28a2f145a9197ea58 | UNDERPOWERED |
| sspec_8c006df3c6338474d80e8d20 | trade_date_block_bootstrap | 9965 | BLOCKED | False | True | surrun_8d91ff8d22a8df8550f6f8f1 | UNDERPOWERED |
| sspec_ea79b474055f324092758c33 | trade_date_block_bootstrap | 9966 | BLOCKED | False | True | surrun_6b82bd926b6e4982d8836507 | UNDERPOWERED |
| sspec_ea79b474055f324092758c33 | trade_date_block_bootstrap | 9967 | BLOCKED | False | True | surrun_ba7bc3a8e619da7363fc7d32 | UNDERPOWERED |
| sspec_ea79b474055f324092758c33 | trade_date_block_bootstrap | 9968 | BLOCKED | False | True | surrun_dc90fdd87ae48160d476adbd | UNDERPOWERED |
| sspec_636f87c6cdc8339b2b527eea | trade_date_block_bootstrap | 9969 | BLOCKED | False | True | surrun_cc1136b27387cb922fd663bd | UNDERPOWERED |
| sspec_636f87c6cdc8339b2b527eea | trade_date_block_bootstrap | 9970 | BLOCKED | False | True | surrun_fb346e9e585bb020cf32d5c7 | UNDERPOWERED |
| sspec_636f87c6cdc8339b2b527eea | trade_date_block_bootstrap | 9971 | BLOCKED | False | True | surrun_bb15a92d1916b5fa90ae860f | UNDERPOWERED |
| sspec_5d1b3bb34fb51da74e6a81aa | trade_date_block_bootstrap | 9972 | BLOCKED | False | True | surrun_25c815454f397bac6d0d85ec | UNDERPOWERED |
| sspec_5d1b3bb34fb51da74e6a81aa | trade_date_block_bootstrap | 9973 | BLOCKED | False | True | surrun_02e917b2be6b004b4a2bdc42 | UNDERPOWERED |
| sspec_5d1b3bb34fb51da74e6a81aa | trade_date_block_bootstrap | 9974 | BLOCKED | False | True | surrun_b7f0163ea7a1920bb333a7af | UNDERPOWERED |
| sspec_184ef312d4cacd5c72165927 | trade_date_block_bootstrap | 9975 | BLOCKED | False | False | surrun_9296358114e5ebbbc5190cb8 | UNDERPOWERED |
| sspec_184ef312d4cacd5c72165927 | trade_date_block_bootstrap | 9976 | BLOCKED | False | False | surrun_73de09f956068b6848e5888f | UNDERPOWERED |
| sspec_184ef312d4cacd5c72165927 | trade_date_block_bootstrap | 9977 | BLOCKED | False | False | surrun_38be0d37985e2058233564a2 | UNDERPOWERED |
| sspec_3998608c3cd16ea1c331304a | trade_date_block_bootstrap | 9978 | BLOCKED | False | True | surrun_24ee07c3d1dc477a6a5dcd82 | UNDERPOWERED |
| sspec_3998608c3cd16ea1c331304a | trade_date_block_bootstrap | 9979 | BLOCKED | False | True | surrun_da081c24452398ef6c35a353 | UNDERPOWERED |
| sspec_3998608c3cd16ea1c331304a | trade_date_block_bootstrap | 9980 | BLOCKED | False | True | surrun_941de2bf425f4d7e705255e0 | UNDERPOWERED |
| sspec_d215dbf6b0842c7563e01148 | trade_date_block_bootstrap | 9981 | BLOCKED | False | True | surrun_5ce6056a72ee2e3888da57ff | UNDERPOWERED |
| sspec_d215dbf6b0842c7563e01148 | trade_date_block_bootstrap | 9982 | BLOCKED | False | True | surrun_0e15abec14e89e0ee78a0b49 | UNDERPOWERED |
| sspec_d215dbf6b0842c7563e01148 | trade_date_block_bootstrap | 9983 | BLOCKED | False | True | surrun_6772bdc0f1b1b0ad25f86b2e | UNDERPOWERED |
| sspec_f8b412aa2ee3c42bc30a733f | trade_date_block_bootstrap | 9984 | BLOCKED | False | True | surrun_5329fe2f5c49008573e9ba5f | UNDERPOWERED |
| sspec_f8b412aa2ee3c42bc30a733f | trade_date_block_bootstrap | 9985 | BLOCKED | False | True | surrun_ffdb4c524ac0bb9fc60b527b | UNDERPOWERED |
| sspec_f8b412aa2ee3c42bc30a733f | trade_date_block_bootstrap | 9986 | BLOCKED | False | True | surrun_89e10d30ca42fe37a6eea276 | UNDERPOWERED |
| sspec_38130bb1d0490830c52517a9 | trade_date_block_bootstrap | 9987 | BLOCKED | False | True | surrun_e778134c4c6762ed9217a333 | UNDERPOWERED |
| sspec_38130bb1d0490830c52517a9 | trade_date_block_bootstrap | 9988 | BLOCKED | False | True | surrun_0fefaa4fa27b20f68cfedec6 | UNDERPOWERED |
| sspec_38130bb1d0490830c52517a9 | trade_date_block_bootstrap | 9989 | BLOCKED | False | True | surrun_c94f1747bf413ecf364cc4b2 | UNDERPOWERED |
| sspec_d0664078d2befab418173b27 | trade_date_block_bootstrap | 9990 | BLOCKED | False | True | surrun_a8dbbd1acf0fda9d2fe114b8 | UNDERPOWERED |
| sspec_d0664078d2befab418173b27 | trade_date_block_bootstrap | 9991 | BLOCKED | False | True | surrun_482d144c0516e4073cfeca02 | UNDERPOWERED |
| sspec_d0664078d2befab418173b27 | trade_date_block_bootstrap | 9992 | BLOCKED | False | True | surrun_e1da8480ebba6d826baeb9b2 | UNDERPOWERED |
| sspec_a6796a695a6c80592f04d075 | trade_date_block_bootstrap | 9993 | BLOCKED | False | False | surrun_d749a272fa8e9eec4d12c4bd | UNDERPOWERED |
| sspec_a6796a695a6c80592f04d075 | trade_date_block_bootstrap | 9994 | BLOCKED | False | False | surrun_ccdb40889b90643865f72d69 | UNDERPOWERED |
| sspec_a6796a695a6c80592f04d075 | trade_date_block_bootstrap | 9995 | BLOCKED | False | False | surrun_80c248072a213dcf56ad827a | UNDERPOWERED |
| sspec_fd9befda353435f0d7a33f4a | trade_date_block_bootstrap | 9996 | BLOCKED | False | True | surrun_8bec0615cd8f31ea2bc82184 | UNDERPOWERED |
| sspec_fd9befda353435f0d7a33f4a | trade_date_block_bootstrap | 9997 | BLOCKED | False | True | surrun_efd64b34043242d7ef85ac84 | UNDERPOWERED |
| sspec_fd9befda353435f0d7a33f4a | trade_date_block_bootstrap | 9998 | BLOCKED | False | True | surrun_8cf8b68ea0018bbebba75e39 | UNDERPOWERED |
| sspec_d01bb0bff1ddff4135316028 | trade_date_block_bootstrap | 9999 | BLOCKED | False | True | surrun_8e43b4522c605a0ce5d14fef | UNDERPOWERED |
| sspec_d01bb0bff1ddff4135316028 | trade_date_block_bootstrap | 10000 | BLOCKED | False | True | surrun_ad1395661bde0b27e066887c | UNDERPOWERED |
| sspec_d01bb0bff1ddff4135316028 | trade_date_block_bootstrap | 10001 | BLOCKED | False | True | surrun_305b3741ab4fc626fb838c3f | UNDERPOWERED |
| sspec_54ee0b3ed80da440676c8c29 | trade_date_block_bootstrap | 10002 | BLOCKED | False | True | surrun_dcf5eb4e0484cca29a2dbdc1 | UNDERPOWERED |
| sspec_54ee0b3ed80da440676c8c29 | trade_date_block_bootstrap | 10003 | BLOCKED | False | True | surrun_ee7c07e1c34c3e156bbe1ac5 | UNDERPOWERED |
| sspec_54ee0b3ed80da440676c8c29 | trade_date_block_bootstrap | 10004 | BLOCKED | False | True | surrun_0925545dafc18b3547b5fc23 | UNDERPOWERED |
| sspec_771ab6d42af4e8469b9a5096 | trade_date_block_bootstrap | 10005 | BLOCKED | False | True | surrun_41f5d48c55160be5a5dabea5 | UNDERPOWERED |
| sspec_771ab6d42af4e8469b9a5096 | trade_date_block_bootstrap | 10006 | BLOCKED | False | True | surrun_11cf1107c1381e154b597f64 | UNDERPOWERED |
| sspec_771ab6d42af4e8469b9a5096 | trade_date_block_bootstrap | 10007 | BLOCKED | False | True | surrun_51ef3cca5316c71eff30b555 | UNDERPOWERED |
| sspec_4c3105d699c5957104a697bc | trade_date_block_bootstrap | 10008 | BLOCKED | False | True | surrun_170f23cf1e18fc0cf3dd3642 | UNDERPOWERED |
| sspec_4c3105d699c5957104a697bc | trade_date_block_bootstrap | 10009 | BLOCKED | False | True | surrun_71a8e36a8ab61270c17b1fab | UNDERPOWERED |
| sspec_4c3105d699c5957104a697bc | trade_date_block_bootstrap | 10010 | BLOCKED | False | True | surrun_201de7e77ae1c59b150dfcf4 | UNDERPOWERED |
| sspec_d4120e7747bee4ee2c84e36c | trade_date_block_bootstrap | 10011 | BLOCKED | False | False | surrun_96ed299ceb7206558e902498 | UNDERPOWERED |
| sspec_d4120e7747bee4ee2c84e36c | trade_date_block_bootstrap | 10012 | BLOCKED | False | False | surrun_1c5241a3e12331af40eb8197 | UNDERPOWERED |
| sspec_d4120e7747bee4ee2c84e36c | trade_date_block_bootstrap | 10013 | BLOCKED | False | False | surrun_af294e30a3fb74ee4d46deff | UNDERPOWERED |
| sspec_26e3e739e1bf8f50fef5fe88 | trade_date_block_bootstrap | 10014 | BLOCKED | False | True | surrun_b4018e1a73d9dc1d481175d1 | UNDERPOWERED |
| sspec_26e3e739e1bf8f50fef5fe88 | trade_date_block_bootstrap | 10015 | BLOCKED | False | True | surrun_741a07d07e8bfeb2fc228dc4 | UNDERPOWERED |
| sspec_26e3e739e1bf8f50fef5fe88 | trade_date_block_bootstrap | 10016 | BLOCKED | False | True | surrun_0f61cc6b319f1034568ff111 | UNDERPOWERED |
| sspec_b8f2c2a8368755105d2b4d82 | trade_date_block_bootstrap | 10017 | BLOCKED | False | True | surrun_278b47ff66e23df1005e485e | UNDERPOWERED |
| sspec_b8f2c2a8368755105d2b4d82 | trade_date_block_bootstrap | 10018 | BLOCKED | False | True | surrun_adab6a4f7528bdb27d97198b | UNDERPOWERED |
| sspec_b8f2c2a8368755105d2b4d82 | trade_date_block_bootstrap | 10019 | BLOCKED | False | True | surrun_f004bfdbf1c0d71d175f14eb | UNDERPOWERED |
| sspec_f4a2854f02095cf852c950fa | trade_date_block_bootstrap | 10020 | BLOCKED | False | True | surrun_e2d659a1775540ac0f5da72d | UNDERPOWERED |
| sspec_f4a2854f02095cf852c950fa | trade_date_block_bootstrap | 10021 | BLOCKED | False | True | surrun_d2ab9205a0a25187a44eb64f | UNDERPOWERED |
| sspec_f4a2854f02095cf852c950fa | trade_date_block_bootstrap | 10022 | BLOCKED | False | True | surrun_6bed5bd5f82bd93634956e96 | UNDERPOWERED |
| sspec_70b6f00ffa3f72cf37c75d03 | trade_date_block_bootstrap | 10023 | BLOCKED | False | True | surrun_7c0256ae1ee9878d9718045f | UNDERPOWERED |
| sspec_70b6f00ffa3f72cf37c75d03 | trade_date_block_bootstrap | 10024 | BLOCKED | False | True | surrun_e4dd805ddaa3ea9a15733438 | UNDERPOWERED |
| sspec_70b6f00ffa3f72cf37c75d03 | trade_date_block_bootstrap | 10025 | BLOCKED | False | True | surrun_c8cfbbe88c494f0d5bddd203 | UNDERPOWERED |
| sspec_47a7f29d36706d35623a1838 | trade_date_block_bootstrap | 10026 | BLOCKED | False | True | surrun_bd64b8979a35baf69bcccb2a | UNDERPOWERED |
| sspec_47a7f29d36706d35623a1838 | trade_date_block_bootstrap | 10027 | BLOCKED | False | True | surrun_da7e51f93f428e630312eb43 | UNDERPOWERED |
| sspec_47a7f29d36706d35623a1838 | trade_date_block_bootstrap | 10028 | BLOCKED | False | True | surrun_641ab5aa360e000104a4f01b | UNDERPOWERED |
| sspec_285c69e19ad111290e7bca26 | trade_date_block_bootstrap | 10029 | BLOCKED | False | False | surrun_bed4bc23ab33799e55436bcb | UNDERPOWERED |
| sspec_285c69e19ad111290e7bca26 | trade_date_block_bootstrap | 10030 | BLOCKED | False | False | surrun_78dbba12f42325413ec04a50 | UNDERPOWERED |
| sspec_285c69e19ad111290e7bca26 | trade_date_block_bootstrap | 10031 | BLOCKED | False | False | surrun_83097425989ba5904d067ce1 | UNDERPOWERED |
| sspec_f49a16ae0487aed01f5d31ff | trade_date_block_bootstrap | 10032 | BLOCKED | False | True | surrun_7d323c122b1e19f4cadc06dc | UNDERPOWERED |
| sspec_f49a16ae0487aed01f5d31ff | trade_date_block_bootstrap | 10033 | BLOCKED | False | True | surrun_93b7ecaacce07d5ad8cf908f | UNDERPOWERED |
| sspec_f49a16ae0487aed01f5d31ff | trade_date_block_bootstrap | 10034 | BLOCKED | False | True | surrun_1c0397443243343d455b83b7 | UNDERPOWERED |
| sspec_aa19848593b5bb715aa189b5 | trade_date_block_bootstrap | 10035 | BLOCKED | False | True | surrun_e7efa646571bd8eddf8e3b64 | UNDERPOWERED |
| sspec_aa19848593b5bb715aa189b5 | trade_date_block_bootstrap | 10036 | BLOCKED | False | True | surrun_2f90a141d85a2e4eb64e3c97 | UNDERPOWERED |
| sspec_aa19848593b5bb715aa189b5 | trade_date_block_bootstrap | 10037 | BLOCKED | False | True | surrun_5402d7a7524c03deb90958cb | UNDERPOWERED |
| sspec_1f228d065dadb325eb5b7126 | trade_date_block_bootstrap | 10038 | BLOCKED | False | True | surrun_d3e453c2f00dc3382bfbb32f | UNDERPOWERED |
| sspec_1f228d065dadb325eb5b7126 | trade_date_block_bootstrap | 10039 | BLOCKED | False | True | surrun_f0b2234853ddd3c81aa2bd59 | UNDERPOWERED |
| sspec_1f228d065dadb325eb5b7126 | trade_date_block_bootstrap | 10040 | BLOCKED | False | True | surrun_151f1fcd017f6e36824c8c4b | UNDERPOWERED |
| sspec_41e47d45e6a2b1a6c8244d15 | trade_date_block_bootstrap | 10041 | BLOCKED | False | True | surrun_ebd16e0b623fd5d48eeb04ce | UNDERPOWERED |
| sspec_41e47d45e6a2b1a6c8244d15 | trade_date_block_bootstrap | 10042 | BLOCKED | False | True | surrun_b570ea5be9c2fc0b8d9b70cd | UNDERPOWERED |
| sspec_41e47d45e6a2b1a6c8244d15 | trade_date_block_bootstrap | 10043 | BLOCKED | False | True | surrun_3f6093e352b58062663c981f | UNDERPOWERED |
| sspec_80e9443ee06411d84204d9bf | trade_date_block_bootstrap | 10044 | BLOCKED | False | True | surrun_82d518e2d73de8cc2cd2195a | UNDERPOWERED |
| sspec_80e9443ee06411d84204d9bf | trade_date_block_bootstrap | 10045 | BLOCKED | False | True | surrun_7a3299cc5422abd8916ab763 | UNDERPOWERED |
| sspec_80e9443ee06411d84204d9bf | trade_date_block_bootstrap | 10046 | BLOCKED | False | True | surrun_73130485660aa32c399bf242 | UNDERPOWERED |
| sspec_554b4f96cdbcab3bb7402097 | trade_date_block_bootstrap | 10047 | BLOCKED | False | False | surrun_1d64973e080761097555be40 | UNDERPOWERED |
| sspec_554b4f96cdbcab3bb7402097 | trade_date_block_bootstrap | 10048 | BLOCKED | False | False | surrun_a4d51f389a7d3d8c869aab32 | UNDERPOWERED |
| sspec_554b4f96cdbcab3bb7402097 | trade_date_block_bootstrap | 10049 | BLOCKED | False | False | surrun_5fc6e28e9d215a91ae75dd19 | UNDERPOWERED |
| sspec_9963dc5c1e94bb0b4b39259c | trade_date_block_bootstrap | 10050 | BLOCKED | False | True | surrun_7813340ae31c6dc2d8547c3b | UNDERPOWERED |
| sspec_9963dc5c1e94bb0b4b39259c | trade_date_block_bootstrap | 10051 | BLOCKED | False | True | surrun_8cf31067a3a1ad9bc71c1d08 | UNDERPOWERED |
| sspec_9963dc5c1e94bb0b4b39259c | trade_date_block_bootstrap | 10052 | BLOCKED | False | True | surrun_2888a9f4f264e1cf4145c0b1 | UNDERPOWERED |
| sspec_93890288887c0acf8f7d613e | trade_date_block_bootstrap | 10053 | BLOCKED | False | True | surrun_5dd23c8cbf555190529686e9 | UNDERPOWERED |
| sspec_93890288887c0acf8f7d613e | trade_date_block_bootstrap | 10054 | BLOCKED | False | True | surrun_8bad856d5319f6e39092068a | UNDERPOWERED |
| sspec_93890288887c0acf8f7d613e | trade_date_block_bootstrap | 10055 | BLOCKED | False | True | surrun_c6f23f5028aaa805f5e9869f | UNDERPOWERED |
| sspec_084f472873d857d306f0e195 | trade_date_block_bootstrap | 10056 | BLOCKED | False | True | surrun_962c5534e3c7fd8467ef4b97 | UNDERPOWERED |
| sspec_084f472873d857d306f0e195 | trade_date_block_bootstrap | 10057 | BLOCKED | False | True | surrun_d5a1aefab30b2fa3c3821df7 | UNDERPOWERED |
| sspec_084f472873d857d306f0e195 | trade_date_block_bootstrap | 10058 | BLOCKED | False | True | surrun_ea1f182423fa22576ac48457 | UNDERPOWERED |
| sspec_4fb1beae2da381f510f11652 | trade_date_block_bootstrap | 10059 | BLOCKED | False | True | surrun_e4673d2838616fda4493391b | UNDERPOWERED |
| sspec_4fb1beae2da381f510f11652 | trade_date_block_bootstrap | 10060 | BLOCKED | False | True | surrun_3f119f3d08037055cd85a59c | UNDERPOWERED |
| sspec_4fb1beae2da381f510f11652 | trade_date_block_bootstrap | 10061 | BLOCKED | False | True | surrun_12f2ec8126075e17c6cd4a37 | UNDERPOWERED |
| sspec_ec135af63f8717d6f58584bc | trade_date_block_bootstrap | 10062 | BLOCKED | False | True | surrun_b3bd62f18910abce83fda9eb | UNDERPOWERED |
| sspec_ec135af63f8717d6f58584bc | trade_date_block_bootstrap | 10063 | BLOCKED | False | True | surrun_75d96d484484c85cf3a4405c | UNDERPOWERED |
| sspec_ec135af63f8717d6f58584bc | trade_date_block_bootstrap | 10064 | BLOCKED | False | True | surrun_27c7851b510f016da3fb7681 | UNDERPOWERED |
| sspec_695b0b6b9197189be6e2a634 | trade_date_block_bootstrap | 10065 | BLOCKED | False | False | surrun_cabc55cce0a3542e5fd7ab57 | UNDERPOWERED |
| sspec_695b0b6b9197189be6e2a634 | trade_date_block_bootstrap | 10066 | BLOCKED | False | False | surrun_dbd8e55053922befefbb9670 | UNDERPOWERED |
| sspec_695b0b6b9197189be6e2a634 | trade_date_block_bootstrap | 10067 | BLOCKED | False | False | surrun_0ea98e8cfb1bb5f88bdf7f67 | UNDERPOWERED |
| sspec_213aa6de8d4fc74089d67853 | trade_date_block_bootstrap | 10068 | BLOCKED | False | True | surrun_fea9e101ebb81d28d5f0fe15 | UNDERPOWERED |
| sspec_213aa6de8d4fc74089d67853 | trade_date_block_bootstrap | 10069 | BLOCKED | False | True | surrun_409b6bcaf6257a51b47985d3 | UNDERPOWERED |
| sspec_213aa6de8d4fc74089d67853 | trade_date_block_bootstrap | 10070 | BLOCKED | False | True | surrun_413bb5dfed731fa73e227f09 | UNDERPOWERED |
| sspec_addaade7e5ead29719adf0b2 | trade_date_block_bootstrap | 10071 | BLOCKED | False | True | surrun_7ab239b009dea8d2f875d5ea | UNDERPOWERED |
| sspec_addaade7e5ead29719adf0b2 | trade_date_block_bootstrap | 10072 | BLOCKED | False | True | surrun_994474b618324add725ef124 | UNDERPOWERED |
| sspec_addaade7e5ead29719adf0b2 | trade_date_block_bootstrap | 10073 | BLOCKED | False | True | surrun_208285131c2ae6245cff893c | UNDERPOWERED |
| sspec_1535d29dc4d77f8e59230e1a | trade_date_block_bootstrap | 10074 | BLOCKED | False | True | surrun_8f7c3e61b0fad64dd7fb11a9 | UNDERPOWERED |
| sspec_1535d29dc4d77f8e59230e1a | trade_date_block_bootstrap | 10075 | BLOCKED | False | True | surrun_d326e46efac27e98a8fd9d53 | UNDERPOWERED |
| sspec_1535d29dc4d77f8e59230e1a | trade_date_block_bootstrap | 10076 | BLOCKED | False | True | surrun_c92fe1b8aa90e7eabc983b3b | UNDERPOWERED |
| sspec_83405df2ef3bebb3e6e33875 | trade_date_block_bootstrap | 10077 | BLOCKED | False | True | surrun_e2911ba84dc887505fde8c5b | UNDERPOWERED |
| sspec_83405df2ef3bebb3e6e33875 | trade_date_block_bootstrap | 10078 | BLOCKED | False | True | surrun_337d29c95f7752909869e21b | UNDERPOWERED |
| sspec_83405df2ef3bebb3e6e33875 | trade_date_block_bootstrap | 10079 | BLOCKED | False | True | surrun_2d3294770071b7ba6cdb2865 | UNDERPOWERED |
| sspec_5eb78fba4f09edef3e87c737 | trade_date_block_bootstrap | 10080 | BLOCKED | False | True | surrun_d05c00136b9a058b08bb1cef | UNDERPOWERED |
| sspec_5eb78fba4f09edef3e87c737 | trade_date_block_bootstrap | 10081 | BLOCKED | False | True | surrun_9e67bda32a1090ed2208a184 | UNDERPOWERED |
| sspec_5eb78fba4f09edef3e87c737 | trade_date_block_bootstrap | 10082 | BLOCKED | False | True | surrun_3295a1daedc4caeb90afc36f | UNDERPOWERED |
| sspec_26f4f6319ac4b2aa48b0d8ee | trade_date_block_bootstrap | 10083 | BLOCKED | False | False | surrun_47af06516b6144a6778f20bb | UNDERPOWERED |
| sspec_26f4f6319ac4b2aa48b0d8ee | trade_date_block_bootstrap | 10084 | BLOCKED | False | False | surrun_06757e0f567998e2c17b603f | UNDERPOWERED |
| sspec_26f4f6319ac4b2aa48b0d8ee | trade_date_block_bootstrap | 10085 | BLOCKED | False | False | surrun_5d672af669dd3e2156d4702f | UNDERPOWERED |
| sspec_506e3508502a09ccb5a439a2 | trade_date_block_bootstrap | 10086 | BLOCKED | False | True | surrun_3b7e4b49a8800f44b0906525 | UNDERPOWERED |
| sspec_506e3508502a09ccb5a439a2 | trade_date_block_bootstrap | 10087 | BLOCKED | False | True | surrun_873c513f45a93ebd49e2292d | UNDERPOWERED |
| sspec_506e3508502a09ccb5a439a2 | trade_date_block_bootstrap | 10088 | BLOCKED | False | True | surrun_e117899d9ddd7d7b3c40e5fd | UNDERPOWERED |
| sspec_628c432fd006f69de08d8b59 | trade_date_block_bootstrap | 10089 | BLOCKED | False | True | surrun_b5eca13d69122f486d058516 | UNDERPOWERED |
| sspec_628c432fd006f69de08d8b59 | trade_date_block_bootstrap | 10090 | BLOCKED | False | True | surrun_7b70aa12ca9fa5d9475b6da6 | UNDERPOWERED |
| sspec_628c432fd006f69de08d8b59 | trade_date_block_bootstrap | 10091 | BLOCKED | False | True | surrun_d009f6afc439dcc0940f1c87 | UNDERPOWERED |
| sspec_de474aed4cb509f5c30a879f | trade_date_block_bootstrap | 10092 | BLOCKED | False | True | surrun_a3f8e391c6719dab18ab3157 | UNDERPOWERED |
| sspec_de474aed4cb509f5c30a879f | trade_date_block_bootstrap | 10093 | BLOCKED | False | True | surrun_51a3444742cb2d2fe316c7e5 | UNDERPOWERED |
| sspec_de474aed4cb509f5c30a879f | trade_date_block_bootstrap | 10094 | BLOCKED | False | True | surrun_d4d9ece24e23c3c2282327d3 | UNDERPOWERED |
| sspec_8507a6e3dcc1b7f2977a2412 | trade_date_block_bootstrap | 10095 | BLOCKED | False | True | surrun_eaf33f9eb608f439e1110ab1 | UNDERPOWERED |
| sspec_8507a6e3dcc1b7f2977a2412 | trade_date_block_bootstrap | 10096 | BLOCKED | False | True | surrun_1c86d3cd84a325fd4183bf4c | UNDERPOWERED |
| sspec_8507a6e3dcc1b7f2977a2412 | trade_date_block_bootstrap | 10097 | BLOCKED | False | True | surrun_4c367967dd1694c13f91f147 | UNDERPOWERED |
| sspec_a78c1d8a1eb0fb7cc0920de6 | trade_date_block_bootstrap | 10098 | BLOCKED | False | True | surrun_04b130dec2d138c8e86811d9 | UNDERPOWERED |
| sspec_a78c1d8a1eb0fb7cc0920de6 | trade_date_block_bootstrap | 10099 | BLOCKED | False | True | surrun_6a0c8c387242b6bbe759cab2 | UNDERPOWERED |
| sspec_a78c1d8a1eb0fb7cc0920de6 | trade_date_block_bootstrap | 10100 | BLOCKED | False | True | surrun_6ab87a20f41562d724bdd8f6 | UNDERPOWERED |
| sspec_e195b78de7df0dbdf592f8aa | trade_date_block_bootstrap | 10101 | BLOCKED | False | False | surrun_2679ed0f606094f22369468b | UNDERPOWERED |
| sspec_e195b78de7df0dbdf592f8aa | trade_date_block_bootstrap | 10102 | BLOCKED | False | False | surrun_fb2b381f29322b609d0697c7 | UNDERPOWERED |
| sspec_e195b78de7df0dbdf592f8aa | trade_date_block_bootstrap | 10103 | BLOCKED | False | False | surrun_556e81bc8b4a42d8e49005c0 | UNDERPOWERED |
| sspec_bb92cb59b890f542415916ec | trade_date_block_bootstrap | 10104 | BLOCKED | False | True | surrun_5aeff82d743e0d59473f6b15 | UNDERPOWERED |
| sspec_bb92cb59b890f542415916ec | trade_date_block_bootstrap | 10105 | BLOCKED | False | True | surrun_238f58579e337e417e5f8033 | UNDERPOWERED |
| sspec_bb92cb59b890f542415916ec | trade_date_block_bootstrap | 10106 | BLOCKED | False | True | surrun_3f57daf2188ea268016ff45f | UNDERPOWERED |
| sspec_c619e94e72d5308c959f41ac | trade_date_block_bootstrap | 10107 | BLOCKED | False | True | surrun_18d64ac122ea87812d3eba8f | UNDERPOWERED |
| sspec_c619e94e72d5308c959f41ac | trade_date_block_bootstrap | 10108 | BLOCKED | False | True | surrun_f3d5826f21787d775c0319d1 | UNDERPOWERED |
| sspec_c619e94e72d5308c959f41ac | trade_date_block_bootstrap | 10109 | BLOCKED | False | True | surrun_e67c7e996f88568ee002d1ca | UNDERPOWERED |
| sspec_f9f9135661b8e6d0e6ed7b2f | trade_date_block_bootstrap | 10110 | BLOCKED | False | True | surrun_7877071d8ca32862c70e0834 | UNDERPOWERED |
| sspec_f9f9135661b8e6d0e6ed7b2f | trade_date_block_bootstrap | 10111 | BLOCKED | False | True | surrun_07015aff6300fb251eb95578 | UNDERPOWERED |
| sspec_f9f9135661b8e6d0e6ed7b2f | trade_date_block_bootstrap | 10112 | BLOCKED | False | True | surrun_30e95e7aa152ce12c4773c1c | UNDERPOWERED |
| sspec_6d55ff64b5993e7ab8aaab3a | trade_date_block_bootstrap | 10113 | BLOCKED | False | True | surrun_00451ea72b3b8dd87a3491f0 | UNDERPOWERED |
| sspec_6d55ff64b5993e7ab8aaab3a | trade_date_block_bootstrap | 10114 | BLOCKED | False | True | surrun_7e7e0e7a5a9b982e440dbcca | UNDERPOWERED |
| sspec_6d55ff64b5993e7ab8aaab3a | trade_date_block_bootstrap | 10115 | BLOCKED | False | True | surrun_bf424bce6a90d68cd44fcc50 | UNDERPOWERED |
| sspec_351bf6b67b45e5d341658a00 | trade_date_block_bootstrap | 10116 | BLOCKED | False | True | surrun_f4f918541fdfaa3a5d7ebf0a | UNDERPOWERED |
| sspec_351bf6b67b45e5d341658a00 | trade_date_block_bootstrap | 10117 | BLOCKED | False | True | surrun_872b2f0e7b1f0dce14e4ed3f | UNDERPOWERED |
| sspec_351bf6b67b45e5d341658a00 | trade_date_block_bootstrap | 10118 | BLOCKED | False | True | surrun_588fd3a6e9fc557a0fd3275b | UNDERPOWERED |
| sspec_eab480c2f09bfdad567e2b33 | trade_date_block_bootstrap | 10119 | BLOCKED | False | False | surrun_e3fff2f0749f0ac44ab71f94 | UNDERPOWERED |
| sspec_eab480c2f09bfdad567e2b33 | trade_date_block_bootstrap | 10120 | BLOCKED | False | False | surrun_3f52409670a9083aad2b3184 | UNDERPOWERED |
| sspec_eab480c2f09bfdad567e2b33 | trade_date_block_bootstrap | 10121 | BLOCKED | False | False | surrun_40049567f46a90fcd252f8db | UNDERPOWERED |
| sspec_16b84147002fcd2b3984a6eb | trade_date_block_bootstrap | 10122 | BLOCKED | False | True | surrun_6486c1ea4b85d79b3e4888b2 | UNDERPOWERED |
| sspec_16b84147002fcd2b3984a6eb | trade_date_block_bootstrap | 10123 | BLOCKED | False | True | surrun_5de601c97f7430c2e5b79ae4 | UNDERPOWERED |
| sspec_16b84147002fcd2b3984a6eb | trade_date_block_bootstrap | 10124 | BLOCKED | False | True | surrun_ddc3b78078773d61195332ab | UNDERPOWERED |
| sspec_7a44550ed000f189822129fc | trade_date_block_bootstrap | 10125 | BLOCKED | False | True | surrun_00dde03ba306151165d3545b | UNDERPOWERED |
| sspec_7a44550ed000f189822129fc | trade_date_block_bootstrap | 10126 | BLOCKED | False | True | surrun_250ca1071a267f59f90b3f5b | UNDERPOWERED |
| sspec_7a44550ed000f189822129fc | trade_date_block_bootstrap | 10127 | BLOCKED | False | True | surrun_c6caf9c31a4f3484554dedb4 | UNDERPOWERED |
| sspec_21ecc3664800a63c27d3aac9 | trade_date_block_bootstrap | 10128 | BLOCKED | False | True | surrun_d65d73bdca04ca36c4c058ef | UNDERPOWERED |
| sspec_21ecc3664800a63c27d3aac9 | trade_date_block_bootstrap | 10129 | BLOCKED | False | True | surrun_0bef9088c589ab81358dbb47 | UNDERPOWERED |
| sspec_21ecc3664800a63c27d3aac9 | trade_date_block_bootstrap | 10130 | BLOCKED | False | True | surrun_9809c44624a5cf8595cc0a53 | UNDERPOWERED |
| sspec_9b7e3ab5a5c6bc26813fca1d | trade_date_block_bootstrap | 10131 | BLOCKED | False | True | surrun_79b0d0c65260e8afcaf94198 | UNDERPOWERED |
| sspec_9b7e3ab5a5c6bc26813fca1d | trade_date_block_bootstrap | 10132 | BLOCKED | False | True | surrun_d9a2bcf55653bbe20ab73bf5 | UNDERPOWERED |
| sspec_9b7e3ab5a5c6bc26813fca1d | trade_date_block_bootstrap | 10133 | BLOCKED | False | True | surrun_f28f1617ece4bbbeb843930a | UNDERPOWERED |
| sspec_e8d6fa29005c5ac73d0a3970 | trade_date_block_bootstrap | 10134 | BLOCKED | False | True | surrun_5a63d4a97c49d08bf050acc9 | UNDERPOWERED |
| sspec_e8d6fa29005c5ac73d0a3970 | trade_date_block_bootstrap | 10135 | BLOCKED | False | True | surrun_08faa720ed698118b200a5be | UNDERPOWERED |
| sspec_e8d6fa29005c5ac73d0a3970 | trade_date_block_bootstrap | 10136 | BLOCKED | False | True | surrun_e2da4d47bb8d60754381b57c | UNDERPOWERED |
| sspec_80f0071931072e4717e09bb9 | trade_date_block_bootstrap | 10137 | BLOCKED | False | False | surrun_b0a649d1c0e2eaa79eaaa16b | UNDERPOWERED |
| sspec_80f0071931072e4717e09bb9 | trade_date_block_bootstrap | 10138 | BLOCKED | False | False | surrun_4df05f9cc379ad45cc8d88c0 | UNDERPOWERED |
| sspec_80f0071931072e4717e09bb9 | trade_date_block_bootstrap | 10139 | BLOCKED | False | False | surrun_231cc58b61d471cc82f67a5c | UNDERPOWERED |
| sspec_5b21922442fb7b0aa261628f | trade_date_block_bootstrap | 10140 | BLOCKED | False | True | surrun_cc6e7ee22ec2311768432563 | UNDERPOWERED |
| sspec_5b21922442fb7b0aa261628f | trade_date_block_bootstrap | 10141 | BLOCKED | False | True | surrun_e1a538600dd48035c525b712 | UNDERPOWERED |
| sspec_5b21922442fb7b0aa261628f | trade_date_block_bootstrap | 10142 | BLOCKED | False | True | surrun_7a156d10426ccc52f54bea43 | UNDERPOWERED |
| sspec_949477f2a35b9d18511a8dd4 | trade_date_block_bootstrap | 10143 | BLOCKED | False | True | surrun_5d77f7b61327fbeb37a0af10 | UNDERPOWERED |
| sspec_949477f2a35b9d18511a8dd4 | trade_date_block_bootstrap | 10144 | BLOCKED | False | True | surrun_69eb93a5dd10e6d2f3ee1d02 | UNDERPOWERED |
| sspec_949477f2a35b9d18511a8dd4 | trade_date_block_bootstrap | 10145 | BLOCKED | False | True | surrun_640ba0a1ff37394c5e8438e4 | UNDERPOWERED |
| sspec_555a0f22c2a7e5756d00223f | trade_date_block_bootstrap | 10146 | BLOCKED | False | True | surrun_d8959656800820bce20966a9 | UNDERPOWERED |
| sspec_555a0f22c2a7e5756d00223f | trade_date_block_bootstrap | 10147 | BLOCKED | False | True | surrun_b0451dc418208ab46beba781 | UNDERPOWERED |
| sspec_555a0f22c2a7e5756d00223f | trade_date_block_bootstrap | 10148 | BLOCKED | False | True | surrun_118b9cb7c6356a8d566efe4e | UNDERPOWERED |
| sspec_e779096edc5474e881518f4e | trade_date_block_bootstrap | 10149 | BLOCKED | False | True | surrun_d341dcf188727edc61ccca6d | UNDERPOWERED |
| sspec_e779096edc5474e881518f4e | trade_date_block_bootstrap | 10150 | BLOCKED | False | True | surrun_21ad5e5ae10eace425de0061 | UNDERPOWERED |
| sspec_e779096edc5474e881518f4e | trade_date_block_bootstrap | 10151 | BLOCKED | False | True | surrun_c6019666f951fc07b863215f | UNDERPOWERED |
| sspec_cf5d9d0c7f963d4bfc761ccd | trade_date_block_bootstrap | 10152 | BLOCKED | False | True | surrun_0a0afc2b4c378e3bd57de322 | UNDERPOWERED |
| sspec_cf5d9d0c7f963d4bfc761ccd | trade_date_block_bootstrap | 10153 | BLOCKED | False | True | surrun_2639fa6cb45fd2deba5002ea | UNDERPOWERED |
| sspec_cf5d9d0c7f963d4bfc761ccd | trade_date_block_bootstrap | 10154 | BLOCKED | False | True | surrun_da9942f1e32ce7a9dd47e4c6 | UNDERPOWERED |
| sspec_d98d99865ada446673549c5c | trade_date_block_bootstrap | 10155 | BLOCKED | False | False | surrun_84571070b020ed3efcc3107c | UNDERPOWERED |
| sspec_d98d99865ada446673549c5c | trade_date_block_bootstrap | 10156 | BLOCKED | False | False | surrun_d467e6cbd436266579977c93 | UNDERPOWERED |
| sspec_d98d99865ada446673549c5c | trade_date_block_bootstrap | 10157 | BLOCKED | False | False | surrun_cf485e035a1e3f655b766d23 | UNDERPOWERED |
| sspec_d5170abfd49dd2f44784b3f9 | trade_date_block_bootstrap | 10158 | BLOCKED | False | True | surrun_1fb97e199de44fd1b606d6ef | UNDERPOWERED |
| sspec_d5170abfd49dd2f44784b3f9 | trade_date_block_bootstrap | 10159 | BLOCKED | False | True | surrun_ce0d80e3bd71c1c7d681f197 | UNDERPOWERED |
| sspec_d5170abfd49dd2f44784b3f9 | trade_date_block_bootstrap | 10160 | BLOCKED | False | True | surrun_2b9b5fa5190e7186a7aeb5fd | UNDERPOWERED |
| sspec_14055ed00532925f29c89d9b | trade_date_block_bootstrap | 10161 | BLOCKED | False | True | surrun_b9c228b39aa3eb7a8faa7694 | UNDERPOWERED |
| sspec_14055ed00532925f29c89d9b | trade_date_block_bootstrap | 10162 | BLOCKED | False | True | surrun_684171f39bb158e6d87920c7 | UNDERPOWERED |
| sspec_14055ed00532925f29c89d9b | trade_date_block_bootstrap | 10163 | BLOCKED | False | True | surrun_d0697996c8a6e54e78a6cac7 | UNDERPOWERED |

## Machinery Inventory

- `SurrogateStudyRun` schema and deterministic serialization live in `src/alpha_system/governance/surrogate_run.py`.
- `surrogate_flag` is threaded through `TrialLedgerRecord`; true surrogate trials are excluded from production variant/family counts.
- `alpha governance surrogate-calibrate` runs seeded surrogate calibrations in caller-supplied isolated namespaces.
- Real-data calibration over the kill-shot StudySpec remains a coordinator runbook step before FUTSUB-P28 kill-shot resume.
