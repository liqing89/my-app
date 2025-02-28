import React from 'react';
import { useState } from 'react';
import { Button, Form,  Select, Layout } from 'antd';

const { Content } = Layout;

const App: React.FC = () => {
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
            <Content style={{ padding: 24, width: '100%' }}>
                <Form layout="vertical" style={{ maxWidth: 600, margin: '0 auto' }}>
                    <Form.Item
                        label="mat"
                        name="eleModel"
                        rules={[{ required: true, message: "can not be empty!" }]}
                    >
                        <Select
                            options={[
                                { value: 'option1', label: 'Option 1' },
                                { value: 'option2', label: 'Option 2' }
                            ]}
                        />
                    </Form.Item>

                    <Form.Item wrapperCol={{ span: 24 }} style={{ textAlign: 'center' }}>
                        <Button
                            type="primary"
                            htmlType="submit"
                            onClick = {getEchoRes}
                        >
                            Submit
                        </Button>
                    </Form.Item>
                </Form>
            </Content>
        </Layout>
    );
};

export default App;