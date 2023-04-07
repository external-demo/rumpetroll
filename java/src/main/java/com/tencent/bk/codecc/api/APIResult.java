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

package com.tencent.bk.codecc.api;

import com.google.common.base.Strings;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;
import com.tencent.bk.codecc.config.common.CheckerDetailAction;
import com.tencent.bk.codecc.config.common.CheckerSetAction;
import com.tencent.bk.codecc.config.common.CodeCCBundle;
import com.tencent.bk.codecc.config.common.CommonInfoAction;
import com.tencent.bk.codecc.config.common.ToolMetaAction;
import com.tencent.bk.codecc.config.project.ProjectConfigAction;
import com.tencent.bk.codecc.docker.Docker;
import com.tencent.bk.codecc.docker.launcher.AbstractDockerLauncher;
import com.tencent.bk.codecc.enums.ConstantName;
import com.tencent.bk.codecc.pojo.checkers.CheckerDetail;
import com.tencent.bk.codecc.pojo.checkers.CheckerDetailVO;
import com.tencent.bk.codecc.pojo.checkers.CheckerProps;
import com.tencent.bk.codecc.pojo.checkers.CheckerSet;
import com.tencent.bk.codecc.pojo.checkers.CheckerSetBase;
import com.tencent.bk.codecc.pojo.checkers.CheckerSetBaseListVO;
import com.tencent.bk.codecc.pojo.checkers.CheckerSetsVO;
import com.tencent.bk.codecc.pojo.common.CommonInfo;
import com.tencent.bk.codecc.pojo.defect.DefectNode;
import com.tencent.bk.codecc.pojo.project.ProjectConfig;
import com.tencent.bk.codecc.pojo.reqrsp.*;
import com.tencent.bk.codecc.pojo.tool.ToolInfo;
import com.tencent.bk.codecc.pojo.ui.UIConfig;
import com.tencent.bk.codecc.tool.ToolScan;
import com.tencent.bk.codecc.utils.BeanUtils;
import com.tencent.bk.codecc.utils.CodeccWeb;
import com.tencent.bk.codecc.utils.FileUtils;
import com.tencent.bk.codecc.utils.HttpUtils;
import com.tencent.bk.codecc.utils.JsonUtil;
import com.tencent.bk.codecc.websocket.ScheduleJob;
import com.tencent.bk.codecc.wrapper.Worker;
import com.tencent.bk.codecc.wrapper.WorkerHandler;
import io.netty.channel.Channel;
import okhttp3.Headers;
import okhttp3.Request;
import okhttp3.Response;
import org.apache.commons.compress.utils.Lists;
import org.apache.commons.lang3.StringUtils;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * 对外接口实现类
 *
 * @version V1.0
 * @date 2021/11/9
 */
public class APIResult {
    private static final Logger LOGGER = LoggerFactory.getLogger(APIResult.class);
    private static final Logger initLogger = LoggerFactory.getLogger("init");

    /**
     * 单例.
     */
    public static APIResult getInstance() {
        return SingletonHolder.INSTANCE;
    }

    private static class SingletonHolder {
        private static final APIResult INSTANCE = new APIResult();
    }

    /**
     * 更新项目配置
     *
     * @param setConfigRequest
     * @return
     */
    public String updateConfig(SetConfigRequest setConfigRequest) {
        BaseEntity result = new BaseEntity();
        result.setApiName(setConfigRequest.getApiName());

        CommonInfo commonInfo = CommonInfoAction.getInstance().getCommonInfo();
        CommonInfoAction.getInstance()
                .setCommonInfoToVo(new CommonInfo.Builder()
                        .gateWayUrl(setConfigRequest.getGateWayUrl())
                        .accountId(setConfigRequest.getAccountId())
                        .accessToken(commonInfo.getAccessToken())
                        .bkTicket(commonInfo.getBkTicket())
                        .build()
                );
        ProjectConfig projectConfigNew = new ProjectConfig.Builder()
                .projectName(setConfigRequest.getProjectName())
                .projectPath(setConfigRequest.getProjectPath())
                .projectCodeCCPath(FileUtils.createPath(setConfigRequest.getProjectPath() + File.separator
                        + CodeCCBundle.message("preci.project.result.folder")))
                .projectCodeCCLogPath(FileUtils.createPath(FileUtils.getPreCIPath() + File.separator
                        + CodeCCBundle.message("preci.project.result.logs.folder")))
                .preCommit(setConfigRequest.getPreCommit())
                .prePush(setConfigRequest.getPrePush())
                .yamlCheckEnable(setConfigRequest.isYamlCheckEnable())
                .dockerCheckEnable(setConfigRequest.isDockerCheckEnable())
                .checkerSetBasesList(setConfigRequest.getCheckerSetBasesList())
                .yamlRelPath(setConfigRequest.getYamlRelPath())
                .build();

        //保存preCommit或prePush
        ProjectConfigAction.getInstance().setPreSCM(setConfigRequest,
                "pre-commit",
                setConfigRequest.getPreCommit().isDiffScanEnable(),
                setConfigRequest.getPreCommit().isAllScanEnable()
        );
        ProjectConfigAction.getInstance().setPreSCM(setConfigRequest,
                "pre-push",
                setConfigRequest.getPrePush().isDiffScanEnable(),
                setConfigRequest.getPrePush().isAllScanEnable()
        );

        //添加.codecc目录到.gitignore文件中
        String gitIgnoreFile = setConfigRequest.getProjectPath() + File.separator + ".gitignore";
        File gitignore = Paths.get(gitIgnoreFile).toFile();
        String[] ignoreStr = new String[] { ".codecc", ".idea", ".vscode" };
        LOGGER.info("修改文件: {}，添加过滤目录{} ", gitIgnoreFile, ignoreStr);
        initLogger.info("修改文件: {}，添加过滤目录{} ", gitIgnoreFile, ignoreStr);
        FileUtils.fileInsertContentIfNotExist(gitignore, Arrays.asList(ignoreStr));

        //保存过滤路径
        if (Objects.nonNull(setConfigRequest.getSkipPath()) && StringUtils.isNotEmpty(setConfigRequest.getSkipPath())) {
            LOGGER.info("保存过滤路径：{} to skipPath", setConfigRequest.getSkipPath());
            projectConfigNew.setSkipPath(Arrays.asList(setConfigRequest.getSkipPath().split(",")));
        } else {
            projectConfigNew.setSkipPath(Arrays.asList(".*/\\.codecc/.*", ".*/\\.git", ".*/\\.git/.*", ".*/\\.svn/.*"));
        }
        //保存白名单
        if (Objects.nonNull(setConfigRequest.getWhitePath())
                && StringUtils.isNotEmpty(setConfigRequest.getWhitePath())) {
            LOGGER.info("保存白名单路径：{} to whitePath", setConfigRequest.getWhitePath());
            projectConfigNew.setWhitePath(Arrays.asList(setConfigRequest.getWhitePath().split(",")));
            List<String> absWhitePathList = new ArrayList<>();
            for (String path : projectConfigNew.getWhitePath()) {
                try {
                    List<String> pathList = FileUtils.traverseWhitePath(path,
                            projectConfigNew.getProjectPath(), setConfigRequest.isDockerCheckEnable());
                    if (!pathList.isEmpty()) {
                        absWhitePathList.addAll(pathList);
                    }
                } catch (Exception e) {
                    LOGGER.error("获取白名单路径失败: ", e);
                }

            }
            if (!absWhitePathList.isEmpty()) {
                LOGGER.info("白名单查找绝对路径：{} to whitePath", absWhitePathList);
                projectConfigNew.setAbsWhitePathList(absWhitePathList);
            }
        }

        ProjectConfig projectConfig = ProjectConfigAction.getInstance()
                .getByProjectPath(setConfigRequest.getProjectPath());
        if (Objects.nonNull(projectConfig)) {
            projectConfigNew.setNewLangList(projectConfig.getNewLangList());
            projectConfigNew.setSelectCheckerSetIdList(projectConfig.getSelectCheckerSetIdList());
            projectConfigNew.setSelectCheckerSetNameList(projectConfig.getSelectCheckerSetNameList());
            projectConfigNew.setSelectToolList(projectConfig.getSelectToolList());
            projectConfigNew.setSelectLangList(projectConfig.getSelectLangList());
            projectConfigNew.setSuffixForSelectTools(projectConfig.getSuffixForSelectTools());

            if (Objects.nonNull(projectConfigNew.getCheckerSetBasesList())) {
                List<String> selectCheckerSetIDList = projectConfigNew.getCheckerSetBasesList().stream()
                        .map(it -> it.getCheckerSetId())
                        .collect(Collectors.toList());
                List<CheckerSet> selectCheckerSetList = CheckerSetAction.getInstance()
                        .getCheckerSetListById(Sets.newHashSet(selectCheckerSetIDList));
                projectConfigNew.setSelectCheckerSet(selectCheckerSetList);
            }
        }

        projectConfig = projectConfigNew;

        if (!CheckerSetAction.getInstance().checkerAction(projectConfig)) {
            result.setStatus("failed");
            LOGGER.error("setConfig 规则处理失败");
            return getConfig(result);
        }

        if (!ProjectConfigAction.getInstance().suffixAction(projectConfig)) {
            result.setStatus("failed");
            LOGGER.error("setConfig 文件后缀处理失败");
            return getConfig(result);
        }
        result.setStatus("success");
        result.setProjectPath(setConfigRequest.getProjectPath());
        return getConfig(result);
    }

    /**
     * 获取规则集列表
     *
     * @return
     */
    public String getCheckerSet() {
        List<CheckerSetBase> checkerSetBaseList = Lists.newArrayList();
        CheckerSetBaseListVO checkerSets = new CheckerSetBaseListVO();
        CheckerSetsVO checkerSetsVO = CheckerSetAction.getInstance().getCheckerSets();
        List<ToolInfo> toolMetaList = ToolMetaAction.getInstance().getToolMeta().getToolMeta();
        CheckerDetailVO checkerDetailVO = CheckerDetailAction.getInstance().getCheckerDetail();
        if (Objects.nonNull(checkerSetsVO)) {
            for (CheckerSet checkerSet : checkerSetsVO.getCheckerSets()) {
                CheckerSetBase checkerSetBase = JsonUtil.fromJson(JsonUtil.toJson(checkerSet),
                        CheckerSetBase.class);
                checkerSetBase.setSupportTools(StringUtils.join(checkerSet.getToolList(), ","));
                for (ToolInfo toolInfo : toolMetaList) {
                    if (checkerSet.getToolList().contains(toolInfo.getName())
                            && Objects.nonNull(toolInfo.getBinary())) {
                        checkerSetBase.setBinaryEnable(true);
                    }
                }
                //添加规则详情
                List<CheckerDetail> checkerDetailList = Lists.newArrayList();
                for (CheckerProps checkerProps : checkerSet.getCheckerProps()) {
                    checkerDetailList.addAll(
                            checkerDetailVO.getCheckerDetailList()
                                    .stream().filter(it ->
                                    it.getToolName().equals(checkerProps.getToolName())
                                            && it.getCheckerKey().equals(checkerProps.getCheckerKey())
                            )
                                    .collect(Collectors.toList())
                    );
                }
                checkerSetBase.setCheckerDetailList(checkerDetailList);

                checkerSetBaseList.add(checkerSetBase);
            }
            checkerSets.setApiName("GET_ALL_CHECKER_SET");
            checkerSets.setCheckerSetBasesList(checkerSetBaseList);
        }
        return JsonUtil.toJson(checkerSets);
    }

    /**
     * 获取规则集列表
     *
     * @return
     */
    public String getCheckerDetail(CheckerDetailReqVO checkerDetailReqVO) {
        CheckerDetail checkerDetail = CheckerDetailAction.getInstance()
                .getCheckerDetail(checkerDetailReqVO.getToolName(), checkerDetailReqVO.getCheckerName());
        checkerDetail.setApiName(checkerDetailReqVO.getApiName());
        return JsonUtil.toJson(checkerDetail);
    }

    /**
     * 获取配置信息
     *
     * @param getConfig
     * @return
     */
    public String getConfig(BaseEntity getConfig) {
        UIConfig uiConfig = null;
        ProjectConfig projectConfig = ProjectConfigAction.getInstance().getByProjectPath(getConfig.getProjectPath());
        if (Objects.isNull(projectConfig)) {
            LOGGER.error("Exception: 获取项目配置信息projectConfig为null");
            return JsonUtil.toJson(uiConfig);
        }
        CommonInfo commonInfo = CommonInfoAction.getInstance().getCommonInfo();
        uiConfig = new UIConfig.Builder()
                .status(getConfig.getStatus())
                .apiName(getConfig.getApiName())
                .accountId(commonInfo.getAccountId())
                .accessToken(commonInfo.getAccessToken())
                .bkTicket(commonInfo.getBkTicket())
                .gateWayUrl(commonInfo.getGateWayUrl())
                .projectPath(projectConfig.getProjectPath())
                .dockerCheckEnable(projectConfig.isDockerCheckEnable())
                .yamlCheckEnable(projectConfig.isYamlCheckEnable())
                .projectName(projectConfig.getProjectName())
                .skipPath(String.join(",", projectConfig.getSkipPath()))
                .whitePath(String.join(",", projectConfig.getWhitePath()))
                .preCommit(projectConfig.getPreCommit())
                .prePush(projectConfig.getPrePush())
                .yamlRelPath(projectConfig.getYamlRelPath())
                .checkerSetBasesList(projectConfig.getCheckerSetBasesList())
                .build();
        return JsonUtil.toJson(uiConfig);
    }

    /**
     * 保存配置信息
     *
     * @param setConfigRequest
     * @return
     */
    public String setConfig(SetConfigRequest setConfigRequest) throws Exception {
        String result = updateConfig(setConfigRequest);
        ProjectConfig projectConfig = ProjectConfigAction.getInstance()
                .getByProjectPath(setConfigRequest.getProjectPath());
        ToolScan.getInstance().initTools(projectConfig);

        return result;
    }

    /**
     * 初始化本地代码检测
     *
     * @param projectPath
     * @param result
     * @return
     */
    private String init(String projectPath, HashMap<String, String> result) throws Exception {

        //获取公共配置数据
        initLogger.info("获取公共配置数据");
        CommonInfoAction.getInstance().getCommonInfo();

        //获取项目配置数据
        initLogger.info("获取项目配置数据");
        ProjectConfig projectConfig = ProjectConfigAction.getInstance().getByProjectPath(projectPath);
        if (Objects.isNull(projectConfig)) {
            initLogger.info("Exception: 获取配置数据为null, 调用初始化接口之前，是否有调用保存配置接口SET_CONFIG？");
            result.put("status", "failed");
            return JsonUtil.toJson(result);
        }

        //清空.codecc目录下的缓存文件
        String source = projectConfig.getProjectPath()
                + File.separator
                + CodeCCBundle.message("preci.project.result.folder")
                + File.separator + "source";
        try {
            if (Paths.get(source).toFile().isDirectory()) {
                LOGGER.info("清空缓存目录{}", source);
                org.apache.commons.io.FileUtils.deleteDirectory(Paths.get(source).toFile());
            }
        } catch (IOException e) {
            LOGGER.error("删除缓存目录{}失败：", source, e);
            return JsonUtil.toJson(result);
        }

        //获取工具信息
        initLogger.info("获取工具信息");
        ToolMetaAction.getInstance().updateToolMetaToVo();
        //获取规则集
        initLogger.info("获取规则集");
        CheckerSetAction.getInstance().updateCheckerSetToVo();
        //获取规则详情
        initLogger.info("获取规则详情");
        CheckerDetailAction.getInstance().updateCheckerDetailToVo();

        //获取新语言，保存已选语言
        initLogger.info("获取语言初始化工具SCC");
        initLogger.info("正在初始化工程语言{}...", projectConfig.getProjectPath());
        ProjectConfigAction.getInstance().saveSelectLangList(projectConfig);

        //规则集处理
        CheckerSetAction.getInstance().checkerAction(projectConfig);

        //保存已选工具支持的文件后缀
        ProjectConfigAction.getInstance().suffixAction(projectConfig);
        initLogger.info("-----------------------------------------------------");
        initLogger.info("本地代码检查:");
        List<String> checkerSetList = null;
        List<String> toolList = null;
        if (projectConfig.isDockerCheckEnable()) {
            initLogger.info("当前工程本地代码检查已被设置为docker扫描形式.可支持的规则集如下:");
            checkerSetList = projectConfig.getCheckerSetBasesList().stream()
                    .map(it -> it.getCheckerSetLang() + ":" + it.getCheckerSetId())
                    .collect(Collectors.toList());
            toolList = projectConfig.getCheckerSetBasesList().stream()
                    .map(it -> it.getSupportTools())
                    .collect(Collectors.toList());
        } else {
            initLogger.info("当前工程本地代码检查已被设置为二进制（非docker）工具扫描形式.可支持的规则集如下:");
            checkerSetList = projectConfig.getCheckerSetBasesList().stream()
                    .filter(it -> it.isBinaryEnable())
                    .map(it -> it.getCheckerSetLang() + ":" + it.getCheckerSetId())
                    .collect(Collectors.toList());
            toolList = projectConfig.getCheckerSetBasesList().stream()
                    .filter(it -> it.isBinaryEnable())
                    .map(it -> it.getSupportTools())
                    .collect(Collectors.toList());
        }
        initLogger.info(StringUtils.join(checkerSetList, ", "));
        initLogger.info("匹配的工具有{}", StringUtils.join(toolList, ","));

        //初始化工具
        ToolScan.getInstance().initTools(projectConfig);
        initLogger.info("PreCI本地代码检查初始化成功");

        initLogger.info("-----------------------------------------------------");
        initLogger.info("云端代码检查:");
        initLogger.info("匹配当前工程对应的云端CodeCC任务");
        initLogger.info("云端代码检查初始化成功");

        initLogger.info("-----------------------------------------------------");
        initLogger.info("AsCode流水线:");
        initLogger.info("检查工程下是否存在yaml文件");
        //yaml检查和docker检查
        if (!ProjectConfigAction.getInstance().checkYamlOption(projectConfig)) {
            result.put("status", "failed");
            initLogger.info("当前工程下不存在yaml文件, 自动生成失败");
            return JsonUtil.toJson(result);
        }
        initLogger.info("当前工程已存在yaml文件");
        initLogger.info("-----------------------------------------------------");
        initLogger.info("PreCI整体初始化成功");

        result.put("status", "success");
        return JsonUtil.toJson(result);
    }

    /**
     * 触发本地代码检测方法
     *
     * @param startScanRequest
     * @return
     */
    public String startScan(StartScanRequest startScanRequest) throws Exception {

        StartScanRspVO startScanRspVO = new StartScanRspVO();
        startScanRspVO.setApiName(startScanRequest.getApiName());
        startScanRspVO.setExtra(startScanRequest.getExtra());
        startScanRspVO.setScanFiles(startScanRequest.getScanFiles());

        JSONObject jsonObject = new JSONObject(getStatus(startScanRequest));
        String resultMsg = "";
        if (jsonObject.get("status").equals(ConstantName.FAILED.getValue())
                || jsonObject.get("TOOL_STATUS").equals(ConstantName.FAILED.getValue())) {
            resultMsg = "项目未初始化";
        }
        if (jsonObject.get("PROJECT_DOCKER_ENABLE").equals(ConstantName.ENABLE.getValue())
                && jsonObject.get("DOCKER_STATUS").equals(ConstantName.FAILED.getValue())) {
            resultMsg = "docker异常";
        }
        if (!Strings.isNullOrEmpty(resultMsg)) {
            LOGGER.error("扫描失败，原因可能为：{} {}", resultMsg, jsonObject.toString());
            startScanRspVO.setDefectNodes(Arrays.asList(new DefectNode.Builder()
                    .checker("扫描失败")
                    .message("原因可能为：" + resultMsg)
                    .filePath(startScanRequest.getProjectPath())
                    .lineNum(0)
                    .build()));
            return JsonUtil.toJson(startScanRspVO);
        }

        //获取项目配置数据
        ProjectConfig projectConfig = ProjectConfigAction.getInstance()
                .getByProjectPath(startScanRequest.getProjectPath());

        List<String> scanFiles = Lists.newArrayList();
        if (startScanRequest.getScanType() != null && startScanRequest.getScanType()
                .equals(ConstantName.INCREMENT.getValue())) {
            startScanRequest.getScanFiles().forEach(path -> {
                File filePath = new File(path);
                if (filePath.exists()) {
                    scanFiles.add(path);
                }
            });
        }

        List<DefectNode> defectNodes = ToolScan.getInstance()
                .inspectFile(scanFiles, startScanRequest.getScanType(), projectConfig, startScanRequest);
        startScanRspVO.setDefectNodes(defectNodes);
        return JsonUtil.toJson(startScanRspVO);
    }

    /**
     * 停止本地代码检测
     *
     * @param stopScan
     * @return
     */
    public String stopScan(BaseEntity stopScan) {
        HashMap<String, String> result = Maps.newHashMap();
        result.put("apiName", stopScan.getApiName());
        //获取项目配置数据
        ProjectConfig projectConfig = ProjectConfigAction.getInstance()
                .getByProjectPath(stopScan.getProjectPath());

        //停止所有扫描
        if (ToolScan.getInstance().stopAllScan(projectConfig)) {
            result.put("status", "success");
        } else {
            result.put("status", "failed");
        }
        return JsonUtil.toJson(result);
    }

    /**
     * 异步调用初始化代码检测
     *
     * @param initRequest
     * @return
     */
    public String asyncInit(SetConfigRequest initRequest) throws Exception {

        HashMap<String, String> result = Maps.newHashMap();
        result.put("apiName", initRequest.getApiName());
        result.put("logPath", System.getProperty("PRECI_LOGS_PATH") + File.separator + "init.log");
        result.put("status", "running");

        initLogger.info(JsonUtil.toJson(result));

        //创建异步初始化包装器
        Worker worker = initWorker(initRequest, result);
        WorkerHandler.getInstance().asyncAction(worker, initLogger);
        return JsonUtil.toJson(result);
    }

    public String ping(BaseEntity request) {
        return JsonUtil.toJson(new HashMap<String, String>() {
            {
                put("apiName", request.getApiName());
                put("status", "success");
            }
        });
    }

    public void initStatus(Channel channel, BaseEntity request) {
        HashMap<String, String> result = Maps.newHashMap();
        result.put("apiName", request.getApiName());
        result.put("status", "success");
        ScheduleJob.getInstance()
                .scheduleCheckInitOption(channel, request.getProjectPath(), result);
    }

    public String getStatus(BaseEntity request) {
        HashMap<String, String> result = Maps.newHashMap();
        result.put("apiName", request.getApiName());
        result.put("status", "success");
        return checkStatus(result, request.getProjectPath());
    }

    /**
     * 实现worker接口初始化调用
     *
     * @param initRequest
     * @param result
     * @return
     */
    private Worker initWorker(SetConfigRequest initRequest, HashMap<String, String> result) throws Exception {
        return new Worker() {
            @Override
            public String action() {
                try {
                    boolean dockerAvailable = ProjectConfigAction.getInstance().checkDockerOption(initRequest);
                    if (!dockerAvailable) {
                        result.put("status", "failed");
                        initLogger.info("Exception: Docker服务启动失败");
                        initLogger.info(JsonUtil.toJson(result) + "\n");
                        return JsonUtil.toJson(result);
                    }

                    CommonInfo commonInfo = CommonInfoAction.getInstance().getCommonInfo();

                    if (!CodeccWeb.getInstance().getAgentStatusFromHttp(commonInfo.getGateWayUrl())) {
                        initLogger.error("初始化失败，原因为：部分agent服务状态异常，请重新启动PreCI服务：preci server --restart");
                        result.put("status", "failed");
                        return JsonUtil.toJson(result);
                    }

                    //保存配置信息
                    JSONObject jsonObject = new JSONObject(updateConfig(initRequest));
                    if (jsonObject.get("status").equals(ConstantName.FAILED.getValue())) {
                        result.put("status", ConstantName.FAILED.getValue());
                        initLogger.info(JsonUtil.toJson(result) + "\n");
                        return JsonUtil.toJson(result);
                    }

                    return init(initRequest.getProjectPath(), result);
                } catch (Exception e) {
                    result.put("status", ConstantName.FAILED.getValue());
                    initLogger.error("初始化失败!");
                    LOGGER.error("初始化失败：", e);
                }
                return JsonUtil.toJson(result);
            }
        };
    }

    /**
     * 实现worker接口初始化调用主逻辑
     *
     * @param projectPath
     * @param result
     * @return
     */
    public String checkStatus(HashMap<String, String> result, String projectPath) {
        result.put("DOCKER_STATUS", "failed");
        result.put("YAML_STATUS", "successful");
        result.put("AGENT_STATUS", "successful");
        result.put("PROJECT_DOCKER_ENABLE", "false");
        ProjectConfig projectConfig = ProjectConfigAction.getInstance()
                .getByProjectPath(projectPath);
        CommonInfo commonInfo = CommonInfoAction.getInstance().getRetainCommonInfo();
        if (Objects.isNull(projectConfig)) {
            result.put("status", "failed");
        } else {
            if (projectConfig.isDockerCheckEnable()) {
                result.put("PROJECT_DOCKER_ENABLE", "true");
                if (AbstractDockerLauncher.getLauncher().dockerAvailable()) {
                    result.put("DOCKER_STATUS", "successful");
                }
            }

            File ymlFile = new File(projectConfig.getProjectPath()
                    + File.separator + projectConfig.getYamlRelPath());
            if (!ymlFile.exists()) {
                result.put("YAML_STATUS", "failed");
            }
        }
        if (Paths.get(projectPath, ".codecc").toFile().isDirectory()) {
            result.put("TOOL_STATUS", "successful");
        } else {
            result.put("TOOL_STATUS", "failed");
        }
        if (!CodeccWeb.getInstance().getAgentStatusFromHttp(commonInfo.getGateWayUrl())) {
            result.put("AGENT_STATUS", "failed");
        }
        return JsonUtil.toJson(result);
    }

    public String getRemoteVersion(BaseEntity request) {
        HashMap<String, String> result = Maps.newHashMap();
        result.put("apiName", request.getApiName());
        result.put("status", "success");
        String depStr = "prod";
        if (StringUtils.isNotEmpty(request.getEnv())) {
            depStr = request.getEnv();
        }
        String remoteVersion = CodeccWeb.getInstance().getRemoteVersionForPreCI(depStr);
        result.put("remoteVersion", remoteVersion);
        return JsonUtil.toJson(result);
    }
}
