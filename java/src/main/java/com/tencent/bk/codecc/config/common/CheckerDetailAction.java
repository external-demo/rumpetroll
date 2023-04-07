/*
 * Tencent is pleased to support the open source community by making BlueKing available.
 * Copyright (C) 2017-2018 THL A29 Limited, a Tencent company. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 * http://opensource.org/licenses/MIT
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.tencent.bk.codecc.config.common;

import com.google.common.collect.Maps;
import com.tencent.bk.codecc.pojo.checkers.CheckerDetail;
import com.tencent.bk.codecc.pojo.checkers.CheckerDetailVO;
import com.tencent.bk.codecc.pojo.reqrsp.CheckerDetailReqVO;
import com.tencent.bk.codecc.utils.AgentEnv;
import com.tencent.bk.codecc.utils.CodeccWeb;
import com.tencent.bk.codecc.utils.FileUtils;
import com.tencent.bk.codecc.utils.JsonUtil;
import com.tencent.bk.codecc.utils.PreSCMScript;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * 规则详情处理类
 * @version V1.0
 * @date 2021/11/11
 */
public class CheckerDetailAction {
    private static final Logger LOGGER = LoggerFactory.getLogger(CheckerDetailAction.class);
    private static CheckerDetailVO checkerDetailVO = new CheckerDetailVO();
    private static String checkerDetailFilePath = FileUtils.getPreCIPath() + File.separator
            + CodeCCBundle.message("preci.codecc.json.folder") + File.separator + "checkerDetail.json";

    /**
     * 单例.
     */
    public static CheckerDetailAction getInstance() {
        return SingletonHolder.INSTANCE;
    }

    private static class SingletonHolder {
        private static final CheckerDetailAction INSTANCE = new CheckerDetailAction();
    }


    /**
     * 获取单个规则详情
     * @return
     */
    public CheckerDetail getCheckerDetail(String toolName, String checker){
        CheckerDetailVO checkerDetailVO = getCheckerDetail();
        if (Objects.nonNull(checkerDetailVO.getCheckerDetailList())
                && !checkerDetailVO.getCheckerDetailList().isEmpty()) {
            for (CheckerDetail checkerDetail: checkerDetailVO.getCheckerDetailList()) {
                if (checkerDetail.getToolName().equals(toolName) && checkerDetail.getCheckerKey().equals(checker)) {
                    return checkerDetail;
                }
            }
        }

        return new CheckerDetail();
    }

    /**
     * 获取规则详情
     * @return
     */
    public CheckerDetailVO getCheckerDetail() {
        if (Objects.nonNull(checkerDetailVO.getCheckerDetailList())
                && !checkerDetailVO.getCheckerDetailList().isEmpty()) {
            return checkerDetailVO;
        }
        File file = new File(checkerDetailFilePath);
        if (file.exists()) {
            try {
                String checkerDetailData = new String(Files.readAllBytes(Paths.get(checkerDetailFilePath)),
                        StandardCharsets.UTF_8);
                checkerDetailVO = JsonUtil.fromJson(checkerDetailData, CheckerDetailVO.class);
            } catch (Exception e) {
                LOGGER.error("读取规则详情失败：",e);
            }
        } else {
            List<CheckerDetail> checkerDetailList = CodeccWeb.getInstance()
                    .getCheckerList(CheckerSetAction.getInstance().getCheckerSets());
            checkerDetailVO.setCheckerDetailList(checkerDetailList);
        }
        return checkerDetailVO;
    }

    /**
     * 更新规则详情到VO
     * @return
     */
    public CheckerDetailVO updateCheckerDetailToVo() {
        List<CheckerDetail> checkerDetailList = CodeccWeb.getInstance()
                .getCheckerList(CheckerSetAction.getInstance().getCheckerSets());
        checkerDetailVO.setCheckerDetailList(checkerDetailList);
        if (!saveCheckerDetailToFile()) {
            LOGGER.error("save CheckerDetail To File failed, please check it!");
        }
        return checkerDetailVO;
    }

    /**
     * 保存规则详情数据到本地文件
     * @return
     */
    public boolean saveCheckerDetailToFile() {
        if (Objects.isNull(checkerDetailVO.getCheckerDetailList())
                || checkerDetailVO.getCheckerDetailList().isEmpty()) {
            LOGGER.info("checkerDetailVO is empty, don't save to checkerDetailFile.");
            return true;
        }
        return FileUtils.saveContentToFile(checkerDetailFilePath, JsonUtil.toJson(checkerDetailVO));
    }

    /**
     * 从缓存中获取规则详情Map，key为"toolName_checkerName"
     *
     * @return
     */
    public Map<String, CheckerDetail> getCheckerMap() {
        checkerDetailVO = getCheckerDetail();
        Map<String, CheckerDetail> checkerMap = Maps.newHashMap();
        if (checkerDetailVO.getCheckerDetailList().size() > 0) {
            checkerMap = checkerDetailVO.getCheckerDetailList().stream().collect(Collectors
                    .toMap(it -> String.format("%s_%s", it.getToolName(), it.getCheckerKey()),
                            Function.identity(), (k, v) -> v));
        }
        return checkerMap;
    }
}
