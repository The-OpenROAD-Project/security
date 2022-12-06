#!/usr/bin/env python3

import argparse
import gzip
import hashlib
import os
import re
import subprocess
import sys

print("Running pre-commit security hook....")

# Limits for rules
file_add_limit    = 20
file_change_limit = 50

# The following patterns are regular expressions and are matched
# case-insensitive.  They are matched anywhere with the string
# and can have leading or trailing characters and still match.

# Blocked paths (unless allowed below).
blocked_path_patterns = [
    r"flow/",
    r"\.gds",
    r"\.lef",
    r"\.def$",
    r"\.cdl",
    r"\.cal",
    r"\.v$",
    r"\.db",
    r"\.lib",
    r"\.t?gz",
    r"\.tar",
    r"tsmc",
    r"intel",
    r"gf\d+", 
    r"\d+lp",    # Invecas
    r"sc\d+",    # ARM-style names
    r"cln\d+",   # eg CLN65 (for ARM)
    r"scc9gena", # Sky90 library
    r"sky90",    # Sky90
    r"b15"       # Intel
]

# Allowed paths are exceptions to blocked paths above.
allowed_path_patterns = [
    r"^\.git/",
    r"^flow/designs",
    r"^flow/docs",
    r"^flow/platforms/nangate45",
    r"^flow/platforms/sky130",
    r"^flow/platforms/asap7",
    r"^flow/platforms/gf180",
    r"^flow/scripts",
    r"^flow/test",
    r"^flow/tutorials",
    r"^flow/util",
    r"^flow/README.md",
    r"^flow/Makefile",
    r"^flow/Makefile.no_drt",
    r"^(tools/OpenROAD/)?src/grt/test",
    r"^(tools/OpenROAD/)?src/ICeWall/test",
    r"^(tools/OpenROAD/)?src/pad/test",
    r"^((tools/OpenROAD/)?src/odb/)?src/[ld]ef(56)?/TEST",
    r"^((tools/OpenROAD/)?src/odb/)?test",
    r"^(tools/OpenROAD/)?src/sta/examples",
    r"^(tools/OpenROAD/)?src/sta/test",
    r"^(tools/OpenROAD/)?src/psm/test",
    r"^(tools/OpenROAD/)?src/cts/test",
    r"^(tools/OpenROAD/)?src/mpl2?/test",
    r"^(tools/OpenROAD/)?src/rcx/test",
    r"^(tools/OpenROAD/)?src/ant/test",
    r"^(tools/OpenROAD/)?src/dbSta/test",
    r"^(tools/OpenROAD/)?src/ifp/test",
    r"^(tools/OpenROAD/)?src/ppl/test",
    r"^(tools/OpenROAD/)?src/dpl/test",
    r"^(tools/OpenROAD/)?src/dpo/test",
    r"^(tools/OpenROAD/)?src/pdn/test",
    r"^(tools/OpenROAD/)?src/replace/test",
    r"^(tools/OpenROAD/)?src/gpl/test",
    r"^(tools/OpenROAD/)?src/rsz/test",
    r"^(tools/OpenROAD/)?src/tap/test",
    r"^(tools/OpenROAD/)?src/par/test",
    r"^(tools/OpenROAD/)?src/drt/test",
    r"^(tools/OpenROAD/)?src/psm/test",
    r"^(tools/OpenROAD/)?src/pdrev/test",
    r"^(tools/OpenROAD/)?src/pdr/test",
    r"^(tools/OpenROAD/)?src/rmp/test",
    r"^(tools/OpenROAD/)?src/pdngen/test",
    r"^(tools/OpenROAD/)?src/PartitionMgr/test",
    r"^(tools/OpenROAD/)?src/TritonCTS/test",
    r"^(tools/OpenROAD/)?src/PDNSim/test",
    r"^(tools/OpenROAD/)?test",
    r"^tools/yosys",
]

# Files may not contain these patterns in their content anywhere (not
# just the changed portion).  All staged files are checked, even
# "allowed" files - there should still be no bad content in allowed
# files.
#
# Uses compiled expression for performance.
block_content_patterns = \
    re.compile(r"""
       gf(?!(180|018))\d\d+ # Disallow gf12 but allow gf180
     | tsmc       # eg tsmc65lp
     | \d+lp      # eg 12LP (for Invecus)
     | \barm\b    # eg ARM
     | cln\d+     # eg CLN65 (for ARM)
     | cypress    # eg Cypress Semiconductor
     | intel(?!l) # eg Intel (but not intelligent)
    """, re.VERBOSE | re.IGNORECASE)

# Files to skip content checks on
skip_content_patterns = [
    r"\.gif$",
    r"\.jpg$",
    r"\.png$",
    r"\.webp$",
    r"\.pdf$",
    r"\.gif$",
    r"\.odt$",
    r"\.xlsx$",
    r"\.ipynb$",
    r"\.a$",
    r"^src/sta/app/sta$",
    r"\.dat$",  # eg POWV9.dat
    r"\.gds(\.orig)?$",
    r"^README.md$",
    r"^(tools/OpenROAD/)?docs/index.(md|rst)$",
    r"^(tools/OpenROAD/)?docs/user/GettingStarted.(md|rst)$",
    r"^flow/README.md$",
    r"^(tools/OpenROAD/)?src/drt/src", # until cleaned up
    r"^(tools/OpenROAD/)?src/drt/cmake", # .../intel/vtune
    r"^(tools/OpenROAD/)?src/gpl/README.md$",
    r"^(tools/OpenROAD/)?third-party/abc",
    r"^(flow/platforms/)?sky130hd/chameleon",
    r"^(flow/designs/)?sky130hd/chameleon",
    r"^tools/yosys/",
    r"^\.git/",
    r"^flow/designs/.*/metadata.*-ok.json$",
    r"^flow/designs/.*/config.mk$",
    r"^flow/designs/.*/config_hier.mk$",
    r"^flow/designs/.*/config_synth.mk$",
    r"^flow/designs/.*/wrappers.tcl$",
    r"^flow/designs/.*/macros.v$",
    r"^flow/designs/src/.*\.sv2v\.v$",
    r"^flow/scripts/add_routing_blk.tcl$",
    r"^flow/scripts/floorplan.tcl$",
    r"^flow/test/core_tests.sh$",
    r"^flow/test/smoke.sh$",
    r"^flow/util/cell-veneer/wrap_stdcells.tcl",
    r"^flow/util/cell-veneer/lefdef.tcl",
    r"^flow/util/calBuffer.py",
    r"^flow/util/calPath.py",
    r"^flow/util/run.sh",
    r"^flow/Makefile$",
]

# For large files we keep an md5 hash of the contents to avoid the expense
# of scanning them with the block_content_patterns regex which is slow.
md5_whitelist = set((
    # OpenROAD
    'e68d7e44ebb11a713753cc3b4127fca8', # test/sky130hs/sky130_fd_sc_hs__tt_025C_1v80.lib
    '63f66e54f4d04b374e60756388e9c116', # test/sky130hs/sky130_fd_sc_hs__tt_025C_1v80.lib for pdn repair channel
    '7a1179ac0a93781ffdb07090ba8cf260', # test/sky130hd/sky130_fd_sc_hd__ff_n40C_1v95.lib
    'b29ffb80bf70e61b7064796c8702eb45', # src/rcx/test/generate_pattern.spefok
    '0f1a956ff22a003be485a678b3877fd5', # src/rcx/test/generate_pattern.defok
    '303c92cc0ec313c0630d84f94313f6ac', # src/rcx/test/generate_pattern.vok
    'e9e4daefed9083224832fbe262d0ea5d', # src/gpl/test/macro03.def
    # old
    'd80867b517b2448febf60860bf663374', # src/gpl/test/large01.defok
    '1129d48daf4119864762d3afae44700c', # src/gpl/test/large01.def
    'f66e8a49010debd35833f159dad1d5c8', # src/gpl/test/large02.defok
    '8ce7ee36cde5a01fca6b800a4090c5dc', # src/gpl/test/large02.def
    'b49d16b2ca57c7dfe2e690bf1b4c0d57', # src/gpl/test/medium03.defok
    '965c8a3c3b424708583d48ee1f9ad931', # src/gpl/test/medium03.def
    '6725a64db47a2c4f3a9eba59c149ef66', # src/gpl/test/medium04.def
    '13bd6497ece4785e873ff699eef79f41', # src/gpl/test/medium04.defok
    # updated
    '48092fdbd5e37998adaef2115871a98a', # src/gpl/test/large01.defok
    '8dd000d1523b1e464ffd5bd247dc481c', # src/gpl/test/large01.ok
    '02f47f3b32749a009a32d912baf4bd4c', # src/gpl/test/large02.defok
    'aaddd7334472fbc27ab6f77ba0335c3b', # src/gpl/test/large02.ok
    'c1997dcf02807f3f73be35106fbd6de5', # src/gpl/test/medium03.defok
    'a88e8d711c4176e2be10b943fda487c6', # src/gpl/test/medium03.ok
    '365fb4b84cf6ff9bbb96ce24270ad008', # src/gpl/test/medium04.defok
    'c15b28dcd183d5da0a31b9383080c392', # src/gpl/test/medium04.ok

    '338775fa5ff59a87225454f9e3fb7d33', # src/pdn/test/soc_bsg_black_parrot_nangate45.defok
    '11c59e5f428eb51deee617620ed585bf', # src/pdn/test/soc_bsg_black_parrot_nangate45.pad_offset.defok
    '0ade01392aacde0bc812c1d00d8af487', # src/pdn/test/pads_black_parrot.defok (old)
    '21851e9df9ecc6764e3f9067d979dc1e', # src/pdn/test/pads_black_parrot.defok (new)
    'e60445d5a3dcb3efd2e003149a5e3347', # src/pdn/test/pads_black_parrot_flipchip.defok (old)
    '543f979cbf751130966023008ae832bd', # src/pdn/test/pads_black_parrot_flipchip.defok (new)

    # OpenROAD-flow-scripts
    '2d74c6a29a8cd18536ec332accfa76d1', # flow/platforms/sky130ram/sky130_sram_1rw1r_80x64_8/sky130_sram_1rw1r_80x64_8.lef
    '17d9ce812cf1b635c392750ac0ec69c3', # flow/platforms/sky130ram/sky130_sram_1rw1r_128x256_8/sky130_sram_1rw1r_128x256_8.lef
    '3d196f7e32be942538db4021fdd72927', # flow/platforms/sky130ram/sky130_sram_1rw1r_64x256_8/sky130_sram_1rw1r_64x256_8.lef
    '3f2e7428931bc5797727ddcd44ecb9c7', # flow/platforms/sky130hs/lib/sky130_fd_sc_hs__tt_100C_1v80.lib
    '3541e22e1ed76cddd2b104c8938b70e7', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SLVT_SS_nldm_201020.lib
    '6756222941e7d68d3c9cb90984c1bf83', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SLVT_TT_nldm_201020.lib
    'a3caea338431c290089ac110a9839f62', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SRAM_FF_nldm_201020.lib
    '557414126cb483fa25a66e3d17f76fe1', # flow/platforms/asap7/lib/asap7sc7p5t_OA_RVT_SS_nldm_201020.lib
    '421d20d1f12945d4979ae1c78da9aa2e', # flow/platforms/asap7/lib/asap7sc7p5t_AO_RVT_SS_nldm_201020.lib
    '35dc584334ba616972838ab7b4eadaea', # flow/platforms/asap7/lib/asap7sc7p5t_AO_LVT_TT_nldm_201020.lib
    '9e56e6d9790f1cd904914b41c6c0faad', # flow/platforms/asap7/lib/asap7sc7p5t_AO_RVT_FF_nldm_201020.lib
    'f514f36645928a32a7fbd1a232420831', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SRAM_SS_nldm_201020.lib
    '1d0a4b12b973072e2b8ac0c2d80d2a08', # flow/platforms/asap7/lib/asap7sc7p5t_OA_RVT_FF_nldm_201020.lib
    'cb552f32d836cee62e8fd8758ace59bc', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SRAM_TT_nldm_201020.lib
    'a8bb2a328dfaede8e653588dc9b1c062', # flow/platforms/asap7/lib/asap7sc7p5t_OA_LVT_TT_nldm_201020.lib
    'c801c520546a03e5fca703e6efaf4d44', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SLVT_FF_nldm_201020.lib
    'c0160f0735003cdda388782b7d3c2956', # flow/platforms/asap7/lib/asap7sc7p5t_AO_RVT_TT_nldm_201020.lib
    'a36d097e6c3d273f91c4ff4645ebd4a1', # flow/platforms/asap7/lib/asap7sc7p5t_AO_LVT_FF_nldm_201020.lib
    '353c6442fd0a631fe92dd1b4b53c7a57', # flow/platforms/asap7/lib/asap7sc7p5t_OA_LVT_FF_nldm_201020.lib
    '4aa64e2f86ac82f74fd7f85755e96de4', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SLVT_TT_nldm_201020.lib
    'b13ff982123b3ec7a3123e987a976266', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SLVT_SS_nldm_201020.lib
    'c5c12056efdf6971aca43fef7f7b93cd', # flow/platforms/asap7/lib/asap7sc7p5t_OA_RVT_TT_nldm_201020.lib
    '73ce20b16bdd41403b3785e592dbee13', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SRAM_FF_nldm_201020.lib
    'f5b5ea21025ddec37e157b563f7f4db8', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SRAM_TT_nldm_201020.lib
    'd3cbcdde427e44edc87e7c750303b6ad', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SRAM_SS_nldm_201020.lib
    'dda503333c1948a41fd17296b8839a09', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SLVT_FF_nldm_201020.lib
    'cdd685451262808f8f77bd8040c8b230', # flow/platforms/asap7/lib/asap7sc7p5t_OA_LVT_SS_nldm_201020.lib
    '6d1b8586754b2cdcde73695662c2ab65', # flow/platforms/asap7/lib/asap7sc7p5t_AO_LVT_SS_nldm_201020.lib
    '87827d7810febeb69a0a19e9af520642', # flow/designs/sky130hd/microwatt/gds/Microwatt_FP_DFFRFile.gds.gz
    '287e146444ded121d259f82dfe8f3a28', # flow/designs/sky130hd/microwatt/gds/RAM512.gds.gz
    'cb1e9c44a755ceebeb846f33c658a0c8', # flow/designs/nangate45/mempool_tile/mempool_tile_wrap.v

    'eeb17d41504b1c00c7f2dcb9068394e9', # flow/platforms/asap7/lib/asap7sc7p5t_AO_LVT_FF_nldm_211120.lib
    'e0bf755d44fbf5bd0ab56e38eff99d30', # flow/platforms/asap7/lib/asap7sc7p5t_AO_LVT_SS_nldm_211120.lib
    '3d34a74024fb048977a2a64d3b877ed4', # flow/platforms/asap7/lib/asap7sc7p5t_AO_LVT_TT_nldm_211120.lib
    '4ab7811f2c051cf52e7acaab6b8f2271', # flow/platforms/asap7/lib/asap7sc7p5t_AO_RVT_FF_nldm_211120.lib
    '40f0f11eb1cf9ed719d7a35bf02f45ed', # flow/platforms/asap7/lib/asap7sc7p5t_AO_RVT_SS_nldm_211120.lib
    '018cca52aa26dd6b5988f602f79573cc', # flow/platforms/asap7/lib/asap7sc7p5t_AO_RVT_TT_nldm_211120.lib
    '4686350746e96c87832a212ccc0e11d1', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SLVT_FF_nldm_211120.lib
    'f8567ed75247fdd4b2045b551f117002', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SLVT_SS_nldm_211120.lib
    'c0eb655da9d8b9065cef83fd2f9e4c41', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SLVT_TT_nldm_211120.lib
    'd2561b1cd20a0d3908ad09c3e21faaa4', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SRAM_FF_nldm_211120.lib
    'c193a820781df58232d955b497d7ea21', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SRAM_SS_nldm_211120.lib
    '86647167cc8baa250b859960f9b533b3', # flow/platforms/asap7/lib/asap7sc7p5t_AO_SRAM_TT_nldm_211120.lib
    'afeae05e16e8dfa6e38908e09d6c8bef', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_LVT_FF_nldm_220122.lib
    'fca677b7a1902ce9b2ab76fe2d86e442', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_LVT_SS_nldm_220122.lib
    'c170651f484eded37af7b010ec201a3d', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_LVT_TT_nldm_220122.lib
    '584031b7f4a68c85843d3da44c67949f', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_RVT_FF_nldm_220122.lib
    'f750a5468f6821139ba137476a208dd7', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_RVT_SS_nldm_220122.lib
    'a6f01b9e832baa8758dde53d9a2fbc93', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_RVT_TT_nldm_220122.lib
    'dff6309638afa2d887d2943e87dd4b4e', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_SLVT_FF_nldm_220122.lib
    '0f3da098783edbb401f5a947d4442432', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_SLVT_SS_nldm_220122.lib
    '5048e252e88012afe9075684e6325f5b', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_SLVT_TT_nldm_220122.lib
    'dd5645097f05929e9a4ffd0ec200dbed', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_SRAM_FF_nldm_220122.lib
    'a95b60c08d73ffd59b6ee71bf6ca969c', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_SRAM_SS_nldm_220122.lib
    'e74f7e5a661aca152f1f8c3a19270e69', # flow/platforms/asap7/lib/asap7sc7p5t_INVBUF_SRAM_TT_nldm_220122.lib
    'cc6c960e268ab3c616409b217d6b0011', # flow/platforms/asap7/lib/asap7sc7p5t_OA_LVT_FF_nldm_211120.lib
    'c53933ff50d6e7bef5b08f339f19d6fa', # flow/platforms/asap7/lib/asap7sc7p5t_OA_LVT_SS_nldm_211120.lib
    '8203bc5cdbda524b76bd28d35e630826', # flow/platforms/asap7/lib/asap7sc7p5t_OA_LVT_TT_nldm_211120.lib
    'c4125f8e2f04e5941d92ab87d5567563', # flow/platforms/asap7/lib/asap7sc7p5t_OA_RVT_FF_nldm_211120.lib
    '273f4ab932786264178704c121a9f3ea', # flow/platforms/asap7/lib/asap7sc7p5t_OA_RVT_SS_nldm_211120.lib
    'ef8ca7b8be646b5b15ccdff776dcfa6d', # flow/platforms/asap7/lib/asap7sc7p5t_OA_RVT_TT_nldm_211120.lib
    '411acd5b95f75cfc1405925ebd11780f', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SLVT_FF_nldm_211120.lib
    'e3807f5e91fcb915fe231d0ce60874cc', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SLVT_SS_nldm_211120.lib
    '698f21638c2040243bce6e57a0afd5ac', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SLVT_TT_nldm_211120.lib
    '71b17cbd42abf6d0d637da126e07772a', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SRAM_FF_nldm_211120.lib
    'ea7a2cd04f43ba04cb366207493b9d09', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SRAM_SS_nldm_211120.lib
    '97d9a921b9af593667db471d6b7bb885', # flow/platforms/asap7/lib/asap7sc7p5t_OA_SRAM_TT_nldm_211120.lib
    '2b6ecf78280b0041b6043f36ae48a459', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_LVT_FF_nldm_220123.lib
    'e94798d2fdbaa028d23cc2f6b5ef34d3', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_LVT_SS_nldm_220123.lib
    '6c736d8c2f831822c45f38724b4ecb11', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_LVT_TT_nldm_220123.lib
    '9ffdf5ebb0392aebaa1c976f8b3101d4', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_RVT_FF_nldm_220123.lib
    '6866ea78346b3ac2a630bbd752a9c50f', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_RVT_SS_nldm_220123.lib
    'b5e4b8552ecb6d07926b0d55a5c6361b', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_RVT_TT_nldm_220123.lib
    'abfc07f4072a571e8835605a9cb5125d', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_SLVT_FF_nldm_220123.lib
    '3d7ec4e7bcc3e4d34609aea76239a9d7', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_SLVT_SS_nldm_220123.lib
    'cc4456a1a6af57c879cab6855aa4a733', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_SLVT_TT_nldm_220123.lib
    'b1c83951043025a8764367e723083cda', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_SRAM_FF_nldm_220123.lib
    '78d7269168f7a8510820267c4821b886', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_SRAM_SS_nldm_220123.lib
    '108a8fab6d1b1a378017bb19efa7c5bb', # flow/platforms/asap7/lib/asap7sc7p5t_SEQ_SRAM_TT_nldm_220123.lib
    '83993851d568ab1d10a81ac7d99aac52', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_LVT_FF_nldm_211120.lib
    '5a023c4b5c68ee8ffa83818d4903e0f5', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_LVT_SS_nldm_211120.lib
    '9c38e88ab287c2004e9eb2875b3b88bf', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_LVT_TT_nldm_211120.lib
    '435aaa1153ef048e05ba455a8fc4e977', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_RVT_FF_nldm_211120.lib
    'f295c7c36e208ae52f8f5d8e17005ca5', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_RVT_SS_nldm_211120.lib
    '1a2d30afdfb8813fb887cc9a7e8853ce', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_RVT_TT_nldm_211120.lib
    '5737757cde74a0f83b640b461fb5a21a', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_SLVT_FF_nldm_211120.lib
    '7ddafeac4c032a4fb5dcd75566925e2a', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_SLVT_SS_nldm_211120.lib
    '1e4b05df7fefb87a8512df34722d592d', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_SLVT_TT_nldm_211120.lib
    'a45990f40a27ffb1a7cc18b49245381c', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_SRAM_FF_nldm_211120.lib
    'ca2737548b647d564cd49491d5405253', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_SRAM_SS_nldm_211120.lib
    '23c466ad629644d475ad9aea70c9d140', # flow/platforms/asap7/lib/asap7sc7p5t_SIMPLE_SRAM_TT_nldm_211120.lib

))

md5_whitelist_cutoff = 15 * 1024 * 1024 # 15 Mb

# Commits to these repos aren't checked as they are
# never to be made public and are intended for confidential
# data.
repos_secure = set((
    '(.*or-\d:)?/platforms/gf12.git',
    '(.*or-\d:)?/platforms/gf55.git',
    '(.*or-\d:)?/platforms/tsmc65lp.git',
    '(.*or-\d:)?/platforms/intel22.git',
    '(.*or-\d:)?/platforms/intel16.git',
    '(.*dfm:)?/home/zf4_projects/OpenROAD-guest/platforms/gf12.git',
    '(.*dfm:)?/home/zf4_projects/OpenROAD-guest/platforms/gf55.git',
    '(.*dfm:)?/home/zf4_projects/OpenROAD-guest/platforms/tsmc65lp.git',
    '(.*dfm:)?/home/zf4_projects/OpenROAD-guest/platforms/intel22.git',
    '(.*dfm:)?/home/zf4_projects/OpenROAD-guest/platforms/intel16.git',
))

def error(msg):
    msg = '\n\nERROR: {}\n\nTo request an exception please file an issue on GitHub' \
      .format(msg)
    sys.exit(msg)


def run_command(command):
    r = subprocess.run(command,
                       stdout=subprocess.PIPE,
                       encoding='utf-8',
                       shell=True)
    r.check_returncode()

    # Split the output into lines
    return r.stdout.rstrip().split('\n')


def check_content(name, args, whole_file=False):
    for pattern in skip_content_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            if args.verbose:
                print("Skipping content check on {}".format(name))
            return

    # Submodules updates will show up as names to be checked but they
    # should have their contents checked when the submodule itself
    # was committed to. Skip them here.
    if os.path.isdir(name):
        print("Skipping content check on subdir {}".format(name))
        return

    if whole_file:
        if os.path.islink(name):
            if args.verbose:
                print("Skipping link", name)
            return

        # Check big files in the md5 whitelist
        size = os.stat(name).st_size
        if size >= md5_whitelist_cutoff:
            with open(name, 'rb') as f:
                contents = f.read()
            md5_hash = hashlib.md5(contents).hexdigest()
            if md5_hash in md5_whitelist:
                if args.verbose:
                    print('Skipping big {} with hash {}',  name, md5_hash)
                return
            else:
                error('File {} is big but not whitelisted (hash {})'.format(name, md5_hash))

        if name.endswith('.gz'):
            with gzip.open(name, mode='rt', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        else:
            with open(name, encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
    else:
        # the : in front of the file name gets the staged version of the
        # file, not what is currently on disk unstaged which could be
        # different (and possibly not contain the keyword).  We check the
        # whole file not just the changed portion.
        lines = run_command('git show :{}'.format(name))
    for cnt, line in enumerate(lines):
        # re.search matches anywhere in the line
        if re.search(block_content_patterns, line):
            msg = "File {} contains blocked content" \
                " on line {} :\n  {}" \
                .format(name,
                        cnt + 1,
                        line)
            error(msg)


def is_blocked(name, args):
    'Is this name blocked by the path patterns?'
    blocked = False
    for pattern in blocked_path_patterns:
        if re.search(pattern, name, re.IGNORECASE):
            blocked = True
            if args.verbose:
                print("{} matches blocked {}".format(name, pattern))
            break
    if blocked:
        for pattern in allowed_path_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                blocked = False
                if args.verbose:
                    print("{} matches allowed {}".format(name, pattern))
                break
    return blocked


def parse_args(args):
    parser = argparse.ArgumentParser(description='Commit checker')
    parser.add_argument('--local', action='store_true')
    parser.add_argument('--report', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    return parser.parse_args(args)


def walk_error(e):
    raise e


def local(top, args):
    """Check the local tree not the git diff.  This is for private to
    public prechecking. """
    for root, dirs, files in os.walk(top,
                                     onerror=walk_error):
        assert(root.startswith(top))
        if root == top:
            root = ''
        else:
            root = root[len(top)+1:]
        for name in files:
            full_name = os.path.join(root, name)
            if is_blocked(full_name, args):
                msg = "File name is blocked: {}".format(full_name)
                error(msg)
            check_content(full_name, args, whole_file=True)


def check_remotes_secure():
    repos = run_command('git remote --verbose')
    # Example line:
    # origin    /home/zf4_projects/OpenROAD-guest/platforms/gf12.git (fetch)
    for line in repos:
        if not line: # local repo (used for testing)
            return False
        (name, url, _) = re.split('\t| \(', line)
        found = False
        for repo_pattern in repos_secure:
            if re.match(repo_pattern, url):
                found = True
                break
        if not found:
            return False
    return True

def main(args):
    # subprocess.run doesn't exist before 3.5
    if sys.version_info < (3, 5):
        sys.exit("Python 3.5 or later is required")

    # Make sure this is running from the top level of the repo
    try:
        top = run_command('git rev-parse --show-toplevel')[0]
    except:
        error('Not running in git repo: {}'.format(os.getcwd()))

    # Make sure we are running from the root (always true as a hook
    # but not if run manually)
    if os.getcwd() != top:
        print('Running from {}'.format(top))
        os.chdir(top)

    if args.local:
        local(top, args)
        return

    if check_remotes_secure():
        print('All git remotes are secure, checking skipped')
        return

    # Get status of the staged files
    lines = run_command('git diff --cached --name-status')
    if len(lines[0]) == 0:
        sys.exit('ERROR: Nothing is staged')

    # Split the lines in status & file.  Filenames containing whitespace
    # are problematic so don't do that.
    lines = [l.split() for l in lines]
    for l in lines:
        if l[0].startswith('R'): # Handle renames
            assert(len(l) == 3)
            l[0] = 'R'  # Strip off score
            del l[1]    # remove old name
        assert(len(l) == 2)     # sanity check : <status> <file>
        assert(len(l[0]) == 1)  # sanity check : <status> is one char

    # Newly added files
    added = [f[1] for f in lines if f[0] == 'A']
    num_added = len(added)

    # Deleted files
    deleted = [f[1] for f in lines if f[0] == 'D']
    num_deleted = len(deleted)

    # This is all other changes, including modify, rename, copy
    num_changed = len(lines) - num_added - num_deleted

    if (args.report):
        print("Added {} (limit: {})".format(num_added, file_add_limit))
        for name in added:
            print("   ", name)
        print("Deleted {} (limit: none)".format(num_deleted))
        for name in deleted:
            print("   ", name)
        print("Changed {} (limit: {})".format(num_changed, file_change_limit))

    # Check: num added
    if num_added > file_add_limit:
        msg = "too many files added: {} vs limit {}".format(num_added,
                                                            file_add_limit)
        error(msg)

    # Check: num changed
    if num_changed > file_change_limit:
        msg = "too many files changed: {} vs limit {}".format(num_changed,
                                                              file_change_limit)
        error(msg)

    # Check: blocked files
    for status, name in lines:
        if is_blocked(name, args):
            msg = "File name is blocked: {}".format(name)
            error(msg)

    # Check: blocked content
    for status, name in lines:
        if status != 'D': # deleted are always ok
            check_content(name, args)

    print("Passed")


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)
