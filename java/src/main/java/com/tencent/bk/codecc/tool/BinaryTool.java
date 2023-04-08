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

package com.tencent.bk.codecc.tool;

import com.google.common.base.Strings;
import com.tencent.bk.codecc.config.common.CodeCCBundle;
import com.tencent.bk.codecc.enums.OSType;
import com.tencent.bk.codecc.pojo.input.InputVO;
import com.tencent.bk.codecc.report.Reporter;
import com.tencent.bk.codecc.utils.AgentEnv;
import com.tencent.bk.codecc.utils.FileUtils;
import com.tencent.bk.codecc.utils.JsonUtil;
import org.apache.commons.compress.utils.Lists;
import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;

/**
 * 二进制工具执行类
 *
 * @version V1.0
 * @date 2022/8/8
 */
public class BinaryTool {
    private static final Logger initLogger = LoggerFactory.getLogger("init");
    private static final Logger LOGGER = LoggerFactory.getLogger(BinaryTool.class);
    private static String toolInstallPath = FileUtils.createPath(FileUtils.getPreCIPath()
            + File.separator
            + CodeCCBundle.message("preci.codecc.bin.tool.folder"));

    /**
     * 单例.
     */
    public static BinaryTool getInstance() {
        return SingletonHolder.INSTANCE;
    }

    private static class SingletonHolder {
        private static final BinaryTool INSTANCE = new BinaryTool();
    }

    /**
     * 控制台下初始化docker
     *
     * @param toolUrl
     * @param toolName
     * @param urlVersion
     * @return
     */
    public String binaryDownload(String toolUrl, String toolName, String urlVersion) throws Exception {
        String toolPath = "";
        Path path = Paths.get(toolInstallPath, toolName, urlVersion);
        initLogger.info("获取二进制工具下载路径:");
        try {
            if (path.toFile().exists()) {
                toolPath = path.toAbsolutePath().toString();
            } else {
                if (!Strings.isNullOrEmpty(toolUrl)) {
                    LOGGER.info("检测到工具有新版本，删除旧版本：{}",
                            Paths.get(toolInstallPath, toolName).toAbsolutePath().toString());
                    org.apache.commons.io.FileUtils.deleteDirectory(Paths.get(toolInstallPath, toolName).toFile());
                    //创建二进制目录
                    LOGGER.info("创建二进制工具路径: {}", path.toAbsolutePath().toString());
                    path.toFile().mkdirs();
                    //下载二进制
                    LOGGER.info("二进制工具下载路径: {}", toolUrl);
                    String fileName = StringUtils.substringAfterLast(toolUrl, "/");
                    String localToolFile = path.toAbsolutePath().toString() + File.separator + fileName;
                    InputStream in = new URL(toolUrl).openStream();
                    Files.copy(in, Paths.get(localToolFile), StandardCopyOption.REPLACE_EXISTING);
                    //解压二进制
                    LOGGER.info("二进制工具解压: {}", localToolFile);
                    FileUtils.unzipFile(localToolFile, path.toAbsolutePath().toString());
                    toolPath = path.toAbsolutePath().toString();
                    //修改文件权限
                    LOGGER.info("二进制工具修改执行权限: {}", path.toAbsolutePath().toString());
                    FileUtils.chmodPath(path.toAbsolutePath().toString(), true, true, true);
                    if (FileUtils.isFile(localToolFile)) {
                        Paths.get(localToolFile).toFile().delete();
                    }
                } else {
                    initLogger.info("{}二进制工具下载路径为空！", toolName);
                    return toolPath;
                }
            }
        } catch (IOException e) {
            if (path.toFile().exists()) {
                path.toFile().delete();
            }
            LOGGER.error("下载二进制工具失败：", e);
            return "";
        }
        initLogger.info(toolPath);
        initLogger.info("{}下载成功", toolName);
        initLogger.info("{}初始化成功", toolName);
        return toolPath;
    }

    /**
     * 二进制工具依赖环境检测
     *
     * @param bin
     * @param version
     * @param toolName
     */
    public void binaryDepCheck(String bin, String version, String toolName) {
        boolean isExist = false;
        initLogger.info("检测{}依赖{}是否存在？", toolName, bin);
        BufferedReader in = null;
        try {
            Process process = Runtime.getRuntime().exec(bin);
            in = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            while ((line = in.readLine()) != null) {
                line = line.toLowerCase();
                initLogger.info(line);
                if (!line.contains(version)) {
                    isExist = true;
                    break;
                }
            }
            if (!isExist) {
                initLogger.info("{}依赖{}未对应版本{}", toolName, bin, version);
            }
            process.destroy();
        } catch (Exception e) {
            LOGGER.error("{} 依赖的 {} 运行失败。", toolName, bin);
        } finally {
            if (Objects.nonNull(in)) {
                try {
                    in.close();
                } catch (IOException ignored) {
                    System.out.println("binaryDepCheck process status fail");
                }
            }
        }
    }

    /**
     * 二进制工具执行方法
     *
     * @param inputFile
     * @param outputFile
     */
    public void execCommand(String inputFile, String outputFile) {
        BufferedReader in = null;
        try {
            String data = new String(Files.readAllBytes(Paths.get(inputFile)), StandardCharsets.UTF_8);
            InputVO inputVo = JsonUtil.fromJson(data, InputVO.class);
            List<String> cmdList = Lists.newArrayList();
            String toolPath = "";
            if (OSType.WINDOWS.equals(AgentEnv.getOS())
                    && Paths.get(inputVo.getWinBinPath()).toFile().exists()) {
                cmdList.add("cmd");
                cmdList.add("/c");
                cmdList.addAll(Arrays.asList(inputVo.getWinCommand().split("##")));
                toolPath = inputVo.getWinBinPath();
            } else if (OSType.LINUX.equals(AgentEnv.getOS())
                    && Paths.get(inputVo.getLinuxBinPath()).toFile().exists()) {
                cmdList.add("/bin/bash");
                cmdList.add("-c");
                cmdList.addAll(Arrays.asList(inputVo.getLinuxCommand().split("##")));
                toolPath = inputVo.getLinuxBinPath();
            } else if (OSType.MACOS.equals(AgentEnv.getOS())
                    && Paths.get(inputVo.getMacBinPath()).toFile().exists()) {
                cmdList.add("/bin/bash");
                cmdList.add("-c");
                cmdList.addAll(Arrays.asList(inputVo.getMacCommand().split("##")));
                toolPath = inputVo.getMacBinPath();
            }
            for (int idx = 0; idx < cmdList.size(); idx++) {
                String cmd = cmdList.get(idx).replace("\"", "");
                if (cmd.contains("{input.json}")) {
                    cmd = cmd.replace("{input.json}", "\""
                            + inputFile.replace("\\", "/") + "\"");
                    cmdList.set(idx, cmd);
                }
                if (cmd.contains("{output.json}")) {
                    cmd = cmd.replace("{output.json}", "\""
                            + outputFile.replace("\\", "/") + "\"");
                    cmdList.set(idx, cmd);
                }
            }
            LOGGER.info("运行路径：{}", toolPath);
            LOGGER.info("运行命令：{}", String.join(" ", cmdList));
            String jdkPath = FileUtils.jdkPathFromAgent(FileUtils.getPreCIPath() + File.separator + "agent");
            String separator = (AgentEnv.getOS() == AgentOS.WINDOWS) ? ";" : ":";
            jdkPath += separator + "bin";
            String[] envP = {"PATH=" + jdkPath + System.getenv("PATH")};
            LOGGER.info("运行环境变量: {}", String.join(" ", envP));
            LOGGER.info("运行开始");
            if (!Strings.isNullOrEmpty(toolPath) && !cmdList.isEmpty()) {
                Process process = Runtime.getRuntime().exec(cmdList.toArray(new String[0]),
                        envP, Paths.get(toolPath).toFile());
                in = new BufferedReader(new InputStreamReader(process.getInputStream()));
                String line;
                while ((line = in.readLine()) != null) {
                    line = line.toLowerCase();
                    LOGGER.info(line);
                }
                process.destroy();
            }
            LOGGER.info("运行结束");
        } catch (Exception e) {
            LOGGER.error("执行二进制工具命令失败：", e);
        } finally {
            if (Objects.nonNull(in)) {
                try {
                    in.close();
                } catch (IOException ignored) {
                    System.out.println("execCommand process status fail");
                }
            }
        }
    }
}
