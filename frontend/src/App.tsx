import React from "react";
import { useState, useEffect } from 'react';
import { Button, Form,  Select, Input } from 'antd';
import { Breadcrumb, Layout, Menu, theme } from 'antd';


const { Header, Content, Footer } = Layout;

// const items = Array.from({ length: 6 }).map((_, index) => ({
//     key: index + 1,
//     label: `nav ${index + 1}`,
// }));

const items = [
    {
        key:"home",
        label:"Home",
    },
    {
        key:"eleModeling",
        label:"电磁建模",
    },
    {
        key:"airboneSimu",
        label:"回波仿真",
    },
    {
        key:"2dimaging",
        label:"二维成像",
    },
    {
        key:"3dimaging",
        label:"三维成像",
    },
];

type FieldType = {
    fc?: number;
    fs?: number;
};

const App: React.FC = () => {
    const {
        token: { colorBgContainer, borderRadiusLG },
    } = theme.useToken();

    const [RadarForm] = Form.useForm();
    // const [loading, setLoading] = useState(false);


    const [response, setResponse] = useState('');
    const getEchoRes = async () => {
        try {
            const res = await fetch('http://localhost:5000/api/echoGen');
            const data = await res.json();
            setResponse(data.message);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    return (
        <Layout style={{ minHeight: '100vh' }}>

            <Header style={{ display: 'flex', alignItems: 'center' }}>
                <div className="demo-logo" />
                <Menu
                    theme="dark"
                    mode="horizontal"
                    defaultSelectedKeys={['2']}
                    items={items}
                    style={{ flex: 1, minWidth: 0 }}
                />
            </Header>

            <Content style={{ padding: '0 48px' }}>
                <Breadcrumb style={{ margin: '16px 0' }}>
                    <Breadcrumb.Item>Home</Breadcrumb.Item>
                    <Breadcrumb.Item>List</Breadcrumb.Item>
                    <Breadcrumb.Item>App</Breadcrumb.Item>
                </Breadcrumb>
                <div
                    style={{
                        background: colorBgContainer,
                        minHeight: 280,
                        padding: 24,
                        borderRadius: borderRadiusLG,
                    }}
                >
                    <div style={{display: "flex", flexDirection: "row", gap: "10px"}}>
                        <div
                            style={{flex: 1, background: "lightblue", padding: "10px"}}
                        >
                            <div
                                style={{flex:1, padding:"10px", textAlign:"left", paddingBottom:"20px"}}
                            >
                                <text
                                    style={{fontSize:"medium"}}
                                >
                                    雷达参数
                                </text>
                            </div>

                            <Form
                                form={RadarForm}
                                name="RadarForm"
                                labelCol={{ span: 8 }}
                                wrapperCol={{ span: 16 }}
                                style={{ maxWidth: 600 }}
                                initialValues={{ remember: true }}
                                // onFinish={onFinish}
                                // onFinishFailed={onFinishFailed}
                                autoComplete="off"
                                onFieldsChange ={
                                    (changedFields: any[], allFields: any[]) => {
                                        setTimeout(() => {
                                            const tgValues = ["fdop", "B", "Vg"];

                                            const updatedValues: Record<string, any> = {};
                                            changedFields.forEach(field => {
                                                if (tgValues.includes(field.name?.[0])) {
                                                    updatedValues[field.name[0]] = field.value;
                                                }
                                            });

                                            if (Object.keys(updatedValues).length > 0) {
                                                const calres = async(updatedValues: Record<string, any>) => {
                                                    try {
                                                        const response = await fetch("http://localhost:5000/calRes", {
                                                            method: "POST",
                                                            headers: {
                                                                "Content-Type": "application/json",
                                                            },
                                                            body: JSON.stringify(updatedValues),
                                                        });
                                                        const result = await response.json();
                                                        console.log("Backend Response:", result);
                                                    } catch (error) {
                                                        console.error("Error sending data to backend:", error);
                                                    }
                                                }
                                            }
                                        }, 500)
                                    }
                                }
                            >
                                <Form.Item
                                    label="导入电磁建模"
                                    name="eleModel"
                                    rules={[{required: true, message: "can not be empty!"}]}
                                >
                                    <Select
                                        options={[
                                            {value: 'option1', label: 'Option 1'},
                                            {value: 'option2', label: 'Option 2'}
                                        ]}
                                    />
                                </Form.Item>

                                <Form.Item<FieldType>
                                    label="中心频率fc"
                                    name="username"
                                    rules={[{ required: true, message: 'Please input your fc!' }]}
                                >
                                    <Input />
                                </Form.Item>

                                <Form.Item<FieldType>
                                    label="采样率fs"
                                    name="fs"
                                    rules={[{ required: true, message: 'Please input your fs!' }]}
                                >
                                    <Input />
                                </Form.Item>

                                <Form.Item<FieldType>
                                    label="脉冲宽度Tp"
                                    name="Tp"
                                    rules={[{ required: true, message: 'Please input your Tp!' }]}
                                >
                                    <Input />
                                </Form.Item>

                                <Form.Item<FieldType>
                                    label="带宽B"
                                    name="B"
                                    rules={[{ required: true, message: 'Please input your B!' }]}
                                >
                                    <Input />
                                </Form.Item>

                                <Form.Item<FieldType>
                                    label="多普勒带宽fdop"
                                    name="fdop"
                                    rules={[{ required: true, message: 'Please input your fdop!' }]}
                                >
                                    <Input />
                                </Form.Item>

                                <Form.Item<FieldType>
                                    label="脉冲重频PRF"
                                    name="PRF"
                                    rules={[{ required: true, message: 'Please input your PRF!' }]}
                                >
                                    <Input />
                                </Form.Item>

                                <Form.Item<FieldType>
                                    label="波束速度Vg"
                                    name="Vg"
                                    rules={[{ required: true, message: 'Please input your Vg!' }]}
                                >
                                    <Input />
                                </Form.Item>

                                {/*<Form.Item<FieldType> name="remember" valuePropName="checked" label={null}>*/}
                                {/*    <Checkbox>Remember me</Checkbox>*/}
                                {/*</Form.Item>*/}

                                {/*<Form.Item label={null}>*/}
                                {/*    <Button type="primary" htmlType="submit">*/}
                                {/*        Submit*/}
                                {/*    </Button>*/}
                                {/*</Form.Item>*/}

                                <Form.Item wrapperCol={{span: 24}} style={{textAlign: 'center'}}>
                                    <Button
                                        type="primary"
                                        htmlType="submit"
                                        onClick={getEchoRes}
                                    >
                                        Submit
                                    </Button>
                                </Form.Item>
                            </Form>
                        </div>

                        <div
                            style={{flex: 1, background: "lightcoral", padding: "10px"}}
                        >
                            右侧内容
                        </div>
                    </div>
                </div>
            </Content>

            <Footer style={{textAlign: 'center'}}>
                SIPL ©{new Date().getFullYear()} Created by Li Qing
            </Footer>

        </Layout>
    );
};

export default App;